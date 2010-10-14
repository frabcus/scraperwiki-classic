from django.contrib.sites.models import Site
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.decorators.http import condition
import textile
import random
from django.conf import settings
from django.utils.encoding import smart_str

from codewiki import models
from codewiki import forms
from api.emitters import CSVEmitter 
import vc
import frontend

import difflib
import re
import csv
import math
import urllib

import StringIO, csv, types
import datetime
import gdata.docs.service

try:                import json
except ImportError: import simplejson as json

def get_code_object_or_none(klass, short_name):
    try:
        return klass.objects.get(short_name=short_name)
    except:
        return None

def code_error_response(klass, short_name, request):
    if klass.unfiltered.filter(short_name=short_name, deleted=True).count() == 1:
        body = 'Sorry, this %s has been deleted by the owner' % klass.__name__
        string = render_to_string('404.html', {'heading': 'Deleted', 'body': body}, context_instance=RequestContext(request))
        return HttpResponseNotFound(string)
    else:
        raise Http404

def code_overview(request, wiki_type, short_name):
    if wiki_type == 'scraper':
        return scraper_overview(request, short_name)
    else:
        return view_overview(request, short_name)

def scraper_overview(request, short_name):
    """
    Shows info on the scraper plus example data.
    """
    user = request.user
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))
    
    #get views that use this scraper
    related_views = models.View.objects.filter(relations=scraper)
    
    #get meta data
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_contributors = scraper.contributors()
    scraper_requesters = scraper.requesters()    
    scraper_tags = Tag.objects.get_for_object(scraper)
    print scraper_requesters
    column_order = scraper.get_metadata('data_columns')
    if not user_owns_it:
        private_columns = scraper.get_metadata('private_columns')
    else:
        private_columns = None

    lscraperrunevents = scraper.scraperrunevent_set.all().order_by("-id")[:1] # can't use date as it's unindexed
    lastscraperrunevent = lscraperrunevents and lscraperrunevents[0] or None

    #get data for this scaper
    data = models.Scraper.objects.data_summary(scraper_id=scraper.guid,
                                               limit=settings.DATA_TABLE_ROWS, 
                                               column_order=column_order,
                                               private_columns=private_columns)

    # replicates output from data_summary_tables
    return render_to_response('codewiki/scraper_overview.html', {
        'scraper_tags': scraper_tags,
        'selected_tab': 'overview',
        'scraper': scraper,
        'lastscraperrunevent':lastscraperrunevent,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        'data': data,
        'scraper_contributors': scraper_contributors,
        'scraper_requesters': scraper_requesters,
        'related_views': related_views,
        'schedule_options': models.SCHEDULE_OPTIONS,
        }, context_instance=RequestContext(request))


def view_admin (request, short_name):
    response = None

    user = request.user
    view = get_code_object_or_none(models.View, short_name=short_name)
    if not view:
        return code_error_response(models.View, short_name=short_name, request=request)

    user_owns_it = (view.owner() == user)

    form = forms.ViewAdministrationForm(instance=view)
    #form.fields['tags'].initial = ", ".join([tag.name for tag in view.tags])
    response = render_to_response('codewiki/view_admin.html', {'selected_tab': 'overview','scraper': view,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    #you can only get here if you are signed in
    if not user.is_authenticated():
        raise Http404

    if request.method == 'POST':
        #is this an ajax post of a single value?
        js = request.POST.get('js', None)
        #single fields saved via ajax
        if js:
            response = HttpResponse()
            response_text = ''
            element_id = request.POST.get('id', None)       
            if element_id == 'divAboutScraper':
                view.description = request.POST.get('value', None)                                                  
                response_text = textile.textile(view.description)

            if element_id == 'hCodeTitle':
                view.title = request.POST.get('value', None)                                                  
                response_text = view.title

            if element_id == 'divEditTags':
                view.tags = ", ".join([tag.name for tag in view.tags]) + ',' + request.POST.get('value', '')                                                  
                response_text = ", ".join([tag.name for tag in view.tags])

            #save view
            view.save()
            response.write(response_text)
        #saved by form 
        else:
            form = forms.ViewAdministrationForm(request.POST, instance=view)
            response =  HttpResponseRedirect(reverse('code_overview', args=[view.wiki_type, view.short_name]))

            if form.is_valid():
                s = form.save()
                s.tags = form.cleaned_data['tags']
            else:
                response = render_to_response('codewiki/scraper_admin.html', {'selected_tab': 'overview','scraper': view,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    # send back whatever responbse we have
    return response
    
    
def scraper_admin (request, short_name):
    response = None

    user = request.user
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)
    user_owns_it = (scraper.owner() == user)

    form = forms.ScraperAdministrationForm(instance=scraper)
    form.fields['tags'].initial = ", ".join([tag.name for tag in scraper.tags])
    response = render_to_response('codewiki/scraper_admin.html', {'selected_tab': 'overview','scraper': scraper,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    #you can only get here if you are signed in
    if not user.is_authenticated():
        raise Http404

    if request.method == 'POST':
        #single fields saved via ajax
        if request.is_ajax():
            response = HttpResponse()
            response_text = ''
            element_id = request.POST.get('id', None)
            if element_id == 'divAboutScraper':
                scraper.description = request.POST.get('value', None)                                                  
                response_text = textile.textile(scraper.description)
                
            if element_id == 'hCodeTitle':
                scraper.title = request.POST.get('value', None)                                                  
                response_text = scraper.title

            if element_id == 'divEditTags':
                scraper.tags = ", ".join([tag.name for tag in scraper.tags]) + ',' + request.POST.get('value', '')                                                  
                response_text = ", ".join([tag.name for tag in scraper.tags])

            if element_id == 'spnRunInterval':
                scraper.run_interval = int(request.POST.get('value', None))
                response_text = models.SCHEDULE_OPTIONS_DICT[scraper.run_interval]

            if element_id == 'publishScraperButton':
                scraper.published = True
                response_text = ''

            #save scraper
            scraper.save()
            response.write(response_text)
            
        #saved by form 
        else:
            form = forms.ScraperAdministrationForm(request.POST, instance=scraper)
            response =  HttpResponseRedirect(reverse('code_overview', args=['scraper', short_name]))

            if form.is_valid():
                s = form.save()
                s.tags = form.cleaned_data['tags']
            else:
                response = render_to_response('codewiki/scraper_admin.html', {'selected_tab': 'overview','scraper': scraper,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    # send back whatever responbse we have
    return response


def scraper_delete_data(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    if scraper.owner() != request.user:
        raise Http404
    if request.POST.get('delete_data', None) == '1':
        models.Scraper.objects.clear_datastore(scraper_id=scraper.guid)
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

# implemented by setting last_run to None
def scraper_schedule_scraper(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    if scraper.owner() != request.user and not request.user.is_staff:
        raise Http404
    if request.POST.get('schedule_scraper', None) == '1':
        scraper.last_run = None
        scraper.save()
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))


def scraper_run_scraper(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    if not request.user.is_staff:
        raise Http404
    if request.POST.get('run_scraper', None) == '1':
        from management.commands.run_scrapers import ScraperRunner
        t = ScraperRunner(scraper, True)
        t.start()
    
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))


# should be generalized to both wikitypes
def scraper_delete_scraper(request, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    if scraper.owner() != request.user:
        raise Http404
    if request.POST.get('delete_scraper', None) == '1':
        scraper.deleted = True
        scraper.save()
        request.notifications.add("Your scraper has been deleted")
        return HttpResponseRedirect('/')
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))


def view_overview (request, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.View, short_name=short_name)
    if not scraper:
        return code_error_response(models.View, short_name=short_name, request=request)

    scraper_tags = Tag.objects.get_for_object(scraper)
    
    #get scrapers used in this view
    related_scrapers = scraper.relations.filter(wiki_type='scraper')
    
    context = {'selected_tab': 'overview', 'scraper': scraper, 'scraper_tags': scraper_tags, 'related_scrapers': related_scrapers, }
    return render_to_response('codewiki/view_overview.html', context, context_instance=RequestContext(request))
    
    
def view_fullscreen (request, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.View, short_name=short_name)
    if not scraper:
        return code_error_response(models.View, short_name=short_name, request=request)

    return render_to_response('codewiki/view_fullscreen.html', {'scraper': scraper}, context_instance=RequestContext(request))

def comments(request, wiki_type, short_name):

    user = request.user
    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()

    scraper_tags = Tag.objects.get_for_object(scraper)

    context = { 'scraper_tags': scraper_tags, 'scraper_owner': scraper_owner, 'scraper_contributors': scraper_contributors,
                   'scraper_followers': scraper_followers, 'selected_tab': 'comments', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }
    return render_to_response('codewiki/comments.html', context, context_instance=RequestContext(request))


def scraper_history(request, wiki_type, short_name):

    user = request.user
    
    # refresh the whole set of commit alerts when we have this message
    if short_name == "updatecommitalertsrev" and user.is_staff:
        lrepopath = (wiki_type == 'view' and settings.VMODULES_DIR or settings.SMODULES_DIR)
        mercurialinterface = vc.MercurialInterface(lrepopath)
        mercurialinterface.updateallcommitalerts()
        return HttpResponse("Updated commit alerts from mercurial for:" + lrepopath, mimetype="text/plain")
    
    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    
    # sift through the alerts filtering on the scraper through the annoying content_type field
    content_type = scraper.content_type() # this one is actually type Code
    
    # The function updatecommitalertsrev() creates Alerts of content_type.  Make sure it's Code type, not Scraper or View type
    history = frontend.models.Alerts.objects.filter(content_type=content_type, object_id=scraper.pk).order_by('-datetime')
    
    dictionary = { 'selected_tab': 'history', 'scraper': scraper, 'history': history,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it, "user":user }
    
    
    # extract the commit log directly from the mercurial repository without referring to the 'Alerts'
    # keeping this type of code up-to-date means we still have the chance to ditch the entire of 
    # the 'Alert' machinery when it becomes too costly to complete
    
    commitlog = [ ]
    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    for commitentry in mercurialinterface.getcommitlog(scraper):
        try:    user = User.objects.get(pk=int(commitentry["userid"]))
        except: user = None
        
        description = commitentry['description']
        commititem = {"rev":commitentry['rev'], "datetime":commitentry["date"], "user":user}
        
        # extract earliesteditor value that has been prepended into the description(commitmessage)
        mearliesteditor = re.match("(.+?)\|\|\|", description)
        if mearliesteditor:
            commititem['earliesteditor'] = mearliesteditor.group(1)
            description = description[mearliesteditor.end(0):]
        else:
            commititem['earliesteditor'] = ""
        
        commititem["description"] = description 
        
        # aggregate in the commitlog
        if commitlog and commititem["earliesteditor"] and commitlog[-1]["earliesteditor"] == commititem["earliesteditor"]:
            lcommititem = commitlog[-1]
            lcommititem["users"].add(commititem["user"])
            lcommititem["lastrev"] = commititem["rev"]
            lcommititem["lastdatetime"] = commititem["datetime"]
            lcommititem["revcount"] += 1
        else:
            commititem["users"] = set([commititem["user"]])
            commititem["firstrev"] = commititem["rev"]
            commititem["lastrev"] = commititem["rev"]
            commititem["firstdatetime"] = commititem["datetime"]
            commititem["lastdatetime"] = commititem["datetime"]
            commititem["revcount"] = 1
            commititem["datetime"] = commititem["datetime"]
            commititem["type"] = "commit"
            commitlog.append(commititem)
    
    # put in the editing duration ranges
    for commititem in commitlog:
        timeduration = commititem["lastdatetime"] - commititem["firstdatetime"]
        commititem["durationminutes"] = "%.1f" % (timeduration.days*24*60 + timeduration.seconds/60.0)
        
    
    # now obtain the run-events and zip together
    itemlog = commitlog
    if scraper.wiki_type == 'scraper':
        runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')
        for runevent in runevents:
            runitem = { "type":"runevent", "runevent":runevent, "datetime":runevent.run_started }
            if runevent.run_ended:
                runitem["runduration"] = runevent.run_ended - runevent.run_started
            itemlog.append(runitem)
        itemlog.sort(key=lambda x: x["datetime"])
    
    itemlog.reverse()
    dictionary["itemlog"] = itemlog
    dictionary["filestatus"] = mercurialinterface.getfilestatus(scraper)
    
    return render_to_response('codewiki/history.html', dictionary, context_instance=RequestContext(request))


def code(request, wiki_type, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1

    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    status = mercurialinterface.getstatus(scraper, rev)

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    dictionary = { 'scraper_tags': scraper_tags, 'selected_tab': 'history', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }

    # overcome lack of subtract in template
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        status["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]

    dictionary["status"] = status
    dictionary["line_count"] = status["code"].count("\n") + 3

    return render_to_response('codewiki/code.html', dictionary, context_instance=RequestContext(request))



def raw_about_markup(request, wiki_type, short_name):
    code_object = get_code_object_or_none(models.Code, short_name=short_name)
    if not code_object:
        return code_error_response(models.Code, short_name=short_name, request=request)

    response = HttpResponse(mimetype='text/x-web-textile')
    response.write(code_object.description)
    return response


        
# see http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
# also inlining the crappy CSVEmitter.to_csv pointless functionality
# this is all painfully inefficient due to the unstructuredness of the datastore 
# and the fact that if you leave the output hanging too long the gateway times out
import time

# see http://stackoverflow.com/questions/1189111/unicode-to-utf8-for-csv-files-python-via-xlrd
# for issues about how the csv model can't handle unicode
def stringnot(v):
    if v == None:
        return ""
    if type(v) in [unicode, str]:
        return v.encode("utf-8")
    return v

def generate_csv(dictlist, offset):
    keylist = [ ]
    keyset = set()
    for row in dictlist:
        if "latlng" in row:   # split the latlng
            row["lat"], row["lng"] = row.pop("latlng") 
        row.pop("date_scraped", None) 
        keyset.update(row.keys())

    for key in sorted(keyset):
        if key not in keylist:
            keylist.append(key)

    fout = StringIO.StringIO()
    writer = csv.writer(fout, dialect='excel')
    if offset == 0:
        writer.writerow([k.encode("utf-8") for k in keylist])
    for rowdict in dictlist:
        writer.writerow([stringnot(rowdict.get(key))  for key in keylist])
    result = fout.getvalue()
    fout.close()
    return result

def stream_csv(scraper, step=5000, max_rows=1000000):
    for offset in range(0, max_rows, step):
        dictlist = models.Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=step, offset=offset)
        
        yield generate_csv(dictlist, offset)
        if len(dictlist) != limit:
            #we'ver reached the end of the data
            break


# see http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
@condition(etag_func=None)
def export_csv(request, short_name):
    """
    This could have been done by having linked directly to the api/csvout, but
    difficult to make the urlreverse for something in a different app code here
    itentical to scraperwiki/web/api/emitters.py CSVEmitter render()
    """
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    response = HttpResponse(stream_csv(scraper), mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % (short_name)
    return response

def export_gdocs_spreadsheet(request, short_name):
    #TODO: this funciton needs to change to cache things on disc and read the size from tehre rather than in memory
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    #get the csv, it's size and choose a title for the file
    title = scraper.title + " - from ScraperWiki.com"
    csv_url = 'http://%s%s' % (Site.objects.get_current().domain,  reverse('export_csv', kwargs={'short_name': scraper.short_name}))

    # the lack of a list of keys for the table makes a more elegant solution difficult to obtain
    # as it is necessary to take a selection of rows in order to derive the set of columns used
    
    row_limit = 5000
    csv_data = generate_csv(models.Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=row_limit), 0)

    document_size = len(csv_data)
    #print "Document size: " + str(document_size)
    percent_of_max = ((float(document_size) / float(settings.GDOCS_UPLOAD_MAX)) * 100) - 100.0

    #if we are within 1% of maximum, don't upload
    if percent_of_max > -1:
        #print "File is " + str(percent_of_max) + "% too large to upload"

        #upload a subset of records with a note at the top and bottom
        #this calculation is a little crude as it assumes each row is of a simular size. To take account of this, a buffer of 5% is added 
        row_buffer = 5
        split = csv_data.split('\n')
        new_row_count = int(math.floor(len(split) / 100.0 * (100 - (percent_of_max + row_buffer))))
        #print "New row count: " + str(new_row_count)

        #set the new title, data and a warning
        title = title + ' [SUBSET ONLY]'

        csv_data = 'THIS IS A SUBSET OF THE DATA ONLY. GOOGLE DOCS LIMITS FILES TO 1MB. DOWNLOAD THE FULL DATASET AS CSV HERE: %s \n' % str(csv_url)
            # csv_data must not be unicode if it is added to a utf8 string
        csv_data = csv_data + '\n'.join(split[0:new_row_count - 1])
    
    elif scraper.record_count > row_limit:
        warning_row = 'THIS IS A SUBSET OF THE DATA ONLY. A MAXIMUM OF %s RECORDS CAN BE UPLOADED FROM SCRAPERWIKI. DOWNLOAD THE FULL DATASET AS CSV HERE: %s' % (str(row_limit), csv_url)
        csv_data = warning_row + csv_data
        
        
    #create client and authenticate
    client = gdata.docs.service.DocsService()
    client.ClientLogin(settings.GDOCS_UPLOAD_USER, settings.GDOCS_UPLOAD_PASSWORD)

    #create a document reference
    ms = gdata.MediaSource(file_handle=StringIO.StringIO(csv_data), content_type=gdata.docs.service.SUPPORTED_FILETYPES['CSV'], content_length=len(csv_data))

    #try to upload it
    #try:
    entry = client.Upload(ms, title, folder_or_uri=settings.GDOCS_UPLOAD_FOLDER_URI)
    
    #redirect
    print "redirecting"
    return HttpResponseRedirect(entry.GetAlternateLink().href)
        
    #except gdata.service.RequestError:
    #    print "failed to upload for some other reason"

def scraper_table(request):
    dictionary = { }
    dictionary["scrapers"] = models.Scraper.objects.filter(published=True).order_by('-created_at')
    dictionary["loggedinusers"] = set([ usercodeediting.user  for usercodeediting in models.UserCodeEditing.objects.filter(user__isnull=False)])
    dictionary["loggedinusers"] = set([ usercodeediting.user  for usercodeediting in models.UserCodeEditing.objects.filter(user__isnull=False)])
    dictionary["numloggedoutusers"] = models.UserCodeEditing.objects.filter(user__isnull=True).count()
    dictionary["numdraftscrapersediting"] = models.UserCodeEditing.objects.filter(code__isnull=True).count()
    dictionary["numpublishedscrapersediting"] = models.UserCodeEditing.objects.filter(code__published=True).count()
    dictionary["numunpublishedscrapersediting"] = models.UserCodeEditing.objects.filter(code__published=False).count()
    dictionary["numpublishedscraperstotal"] = dictionary["scrapers"].count()
    dictionary["numunpublishedscraperstotal"] = models.Scraper.objects.filter(published=False).count()
    dictionary["numdeletedscrapers"] = models.Scraper.unfiltered.filter(deleted=True).count()
    dictionary["user"] = request.user
    return render_to_response('codewiki/scraper_table.html', dictionary, context_instance=RequestContext(request))
    


def download(request, short_name):
    """
    TODO: DELETE?
    """
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    response = HttpResponse(scraper.saved_code(), mimetype="text/plain")
    response['Content-Disposition'] = \
        'attachment; filename=%s.py' % (scraper.short_name)
    return response


def follow (request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    user = request.user
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    # add the user to follower list
    scraper.add_user_role(user, 'follow')
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)


def unfollow(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    user = request.user
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    # remove the user from follower list
    scraper.unfollow(user)
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)


def twisterstatus(request):
    if 'value' not in request.POST:
        return HttpResponse("needs value=")
    tstatus = json.loads(request.POST.get('value'))

    twisterclientnumbers = set()  # used to delete the ones that no longer exist

    # we are making objects in django to represent the objects in twister for editor windows open
    for client in tstatus["clientlist"]:
        # fixed attributes of the object
        twisterclientnumber = client["clientnumber"]
        twisterclientnumbers.add(twisterclientnumber)
        try:
            user = client['username'] and User.objects.get(username=client['username']) or None
            scraper = client['guid'] and models.Scraper.objects.get(guid=client['guid']) or None
        except:
            continue

        # identify or create the editing object
        try:
            usercodeediting = models.UserCodeEditing.objects.create(user=user, code=scraper, twisterclientnumber=twisterclientnumber)
            usercodeediting.editingsince = datetime.datetime.now()
        except IntegrityError:
            usercodeediting = models.UserCodeEditing.objects.get(twisterclientnumber=twisterclientnumber)

        assert models.UserCodeEditing.objects.filter(twisterclientnumber=twisterclientnumber).count() == 1, client

        # updateable values of the object
        usercodeediting.twisterscraperpriority = client['scrapereditornumber']

        # this condition could instead reference a running object
        if client['running'] and not usercodeediting.runningsince:
            usercodeediting.runningsince = datetime.datetime.now()
        if not client['running'] and usercodeediting.runningsince:
            usercodeediting.runningsince = None

        usercodeediting.save()

    # discard now closed values of the object
    for usercodeediting in models.UserCodeEditing.objects.all():
        if usercodeediting.twisterclientnumber not in twisterclientnumbers:
            usercodeediting.delete()
            # or could use the field: closedsince  = models.DateTimeField(blank=True, null=True)
    return HttpResponse("Howdy ppp ")

def htmlview(request, short_name):
    view = get_code_object_or_none(models.View, short_name=short_name)
    if not view:
        return code_error_response(models.View, short_name=short_name, request=request)

    return HttpResponse(view.saved_code())

def commit_event(request, event_id):
    event = get_object_or_404(models.CodeCommitEvent, id=event_id)
    return render_to_response('codewiki/commit_event.html', {'event': event}, context_instance=RequestContext(request))

def choose_template(request, wiki_type):

    #get templates
    templates = models.Code.objects.filter(isstartup=True, wiki_type=wiki_type).order_by('language')
    
    sourcescraper = request.GET.get('sourcescraper', '')
    
    #choose template (ajax vs normal)
    template = 'codewiki/choose_template.html'
    if request.GET.get('ajax', False):
        template = 'codewiki/includes/choose_template.html'
        
    return render_to_response(template, {'wiki_type': wiki_type, 'templates': templates, 
                                         'languages': [ ll[0]   for ll in models.code.LANGUAGES ], 
                                         'sourcescraper':sourcescraper }, 
                              context_instance=RequestContext(request))


    
def delete_draft(request):
    if request.session.get('ScraperDraft', False):
        del request.session['ScraperDraft']

    # Remove any pending notifications, i.e. the "don't worry, your scraper is safe" one
    request.notifications.used = True

    return HttpResponseRedirect(reverse('frontpage'))

def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if not code:
        return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')

    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    result = '\n'.join(difflib.unified_diff(scraper.saved_code().splitlines(), code.splitlines(), lineterm=''))
    return HttpResponse("::::" + result, mimetype='text')

def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')

    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        result = "%s:::sElEcT rAnGe:::%s" % (json.dumps(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        result = newcode
    return HttpResponse(result, mimetype="text/plain")

#save a code object
def save_code(code_object, user, code_text, earliesteditor, commitmessage):

    code_object.line_count = int(code_text.count("\n"))
    
    # perhaps the base class should call the upper class updates, not the other way round
    if code_object.wiki_type == "scraper":
        code_object.save()  # save the object using the base class (otherwise causes a major failure if it doesn't exist)
        code_object.scraper.update_meta()
        code_object.scraper.save()
    else:
        code_object.update_meta()
        code_object.save()   

    # save code and commit code through the mercurialinterface
    lcommitmessage = earliesteditor and ("%s|||%s" % (earliesteditor, commitmessage)) or commitmessage
    mercurialinterface = vc.MercurialInterface(code_object.get_repo_path())
    mercurialinterface.save(code_object, code_text)
    rev = mercurialinterface.commit(code_object, message=lcommitmessage, user=user)
    mercurialinterface.updatecommitalertsrev(rev)

    # Add user roles
    if code_object.owner():
        if code_object.owner().pk != user.pk:
            code_object.add_user_role(user, 'editor')
    else:
        code_object.add_user_role(user, 'owner')

# Handle Session Draft
# A non-served page for saving scrapers that have been stored in the session for non-signed in users
def handle_session_draft(request, action):

    # check if they are signed in, if no, they shouldent be here, off to the signin page
    if not request.user.is_authenticated():
        response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
        return HttpResponseRedirect(response_url)

    #check if anything in the session        
    session_scraper_draft = request.session.pop('ScraperDraft', None)

    # shouldn't be here
    if not session_scraper_draft:
        response_url = reverse('frontpage')
        return HttpResponseRedirect(response_url)

    draft_scraper = session_scraper_draft.get('scraper', None)
    draft_scraper.save()
    #draft_commit_message = action.startswith('commit') and session_scraper_draft.get('commit_message') or None
    draft_code = session_scraper_draft.get('code')

    commitmessage = request.POST.get('commit_message', "")
    earliesteditor = request.POST.get('earliesteditor', "")
    save_code(draft_scraper, request.user, draft_code, earliesteditor, commitmessage)

    # work out where to send them next
    #go to the scraper page if commited, or the editor if not
    if action == 'save':
        response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})
    elif action == 'commit':
        response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})

    return HttpResponseRedirect(response_url)

# called from the edit function
def saveeditedscraper(request, lscraper):
    form = forms.editorForm(request.POST, instance=lscraper)
    
    #validate
    if not form.is_valid() or 'action' not in request.POST:
        return HttpResponse(json.dumps({'status' : 'Failed'}))

    action = request.POST.get('action').lower()
    # assert action == 'commit'

    # recover the altered object from the form, without saving it to django database - http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method
    scraper = form.save(commit=False)
    if not scraper.guid:
        scraper.buildfromfirsttitle()

    # Add some more fields to the form
    code = form.cleaned_data['code']
    
    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        commitmessage = request.POST.get('commit_message', "")
        earliesteditor = request.POST.get('earliesteditor', "")
        save_code(scraper, request.user, code, earliesteditor, commitmessage)  

        # Work out the URL to return in the JSON object
        url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name':scraper.short_name})
        if action.startswith("commit"):
            response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})

        # Build the JSON object and return it
        res = json.dumps({'redirect':'true', 'url':response_url,})
        return HttpResponse(res)

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'commit_message': request.POST.get('commit_message')}
        request.session['ScraperDraft'] = draft_session_scraper

        # Set a message with django_notify telling the user their scraper is safe
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        scraper.action = action

        status = 'Failed'
        response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})
        if action == 'save':
            status = 'OK'
        elif action == 'commit':
            #!response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
            status = 'OK'

        return HttpResponse(json.dumps({'status':status, 'draft':'True', 'url':response_url}))


def edittutorial(request, short_name):
    code = get_code_object_or_none(models.Code, short_name=short_name)
    if not code:
        return code_error_response(models.Code, short_name=short_name, request=request)

    qtemplate = "?template="+code.short_name
    return HttpResponseRedirect(reverse('editor', args=[code.wiki_type, code.language]) + qtemplate)



#Editor form
blankstartupcode = { 'scraper' : { 'python': "# Blank Python\n", 
                                    'php':   "<?php\n# Blank PHP\n?>\n", 
                                    'ruby':  "# Blank Ruby\n" 
                                 }, 
                     'view'    : { 'python': "# Blank Python\nsourcescraper = ''\n", 
                                   'php':    "<?php\n# Blank PHP\n$sourcescraper = ''\n?>\n", 
                                   'ruby':   "# Blank Ruby\nsourcescraper = ''\n" 
                                  }
                   }

def edit(request, short_name='__new__', wiki_type='scraper', language='python'):
    #return url (where to exit the editor to)
    return_url = reverse('frontpage')

    language = language.lower()

    # identify the scraper (including if there was a draft one backed up)
    has_draft = False
    if request.session.get('ScraperDraft', None):
        draft = request.session['ScraperDraft'].get('scraper', None)
        if draft:
            has_draft  = True

    commit_message = ''
    if has_draft:
        scraper = draft
        commit_message = request.session['ScraperDraft'].get('commit_message', '')        
        code = request.session['ScraperDraft'].get('code', ' missing')

    # Try and load an existing scraper
    elif short_name is not "__new__":
        scraper = get_code_object_or_none(models.Code, short_name=short_name)
        if not scraper:
            return code_error_response(models.Code, short_name=short_name, request=request)
        code = scraper.saved_code()
        return_url = reverse('code_overview', args=[scraper.wiki_type, scraper.short_name])
        if not scraper.published:
            commit_message = 'Scraper created'

    # Create a new scraper
    else:
        if language not in ['python', 'php', 'ruby']:
            language = 'python'

        scraper = None
        if wiki_type == 'scraper':
            scraper = models.Scraper()
        elif  wiki_type == 'view':
            scraper = models.View()
        else:
            raise Exception, "Invalid wiki type"

        startupcode = blankstartupcode[wiki_type][language]
        statuptemplate = request.GET.get('template', False)
        if statuptemplate:
            try:
                templatescraper = models.Code.objects.get(published=True, language=language, short_name=statuptemplate)  # wiki_type as well?
                startupcode = templatescraper.saved_code()
                
            
            except models.Code.DoesNotExist:
                startupcode = startupcode.replace("Blank", "Missing template for")
            
        # replaces the phrase: sourcescraper = 'working-example' with sourcescraper = 'replacement-name'
        inputscrapername = request.GET.get('sourcescraper', False)
        if inputscrapername:
            startupcode = re.sub('''(?<=sourcescraper = ["']).*?(?=["'])''', inputscrapername, startupcode)
        
        scraper.language = language
        code = startupcode


    # if it's a post-back (save) then execute that
    if request.POST:
        return saveeditedscraper(request, scraper)
    else:
        # Else build the page
        form = forms.editorForm(instance=scraper)
        form.fields['code'].initial = code

        tutorial_scrapers = models.Code.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')

    context = {}
    context['form'] = form
    context['scraper'] = scraper
    context['has_draft'] = has_draft
    context['user'] = request.user
    context['quick_help_template'] = 'codewiki/includes/quick_help_%s.html' % scraper.language.lower()
    context['selected_tab'] = 'code'
    return render_to_response('codewiki/editor.html', context, context_instance=RequestContext(request))

