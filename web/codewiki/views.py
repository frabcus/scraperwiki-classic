from django.contrib.sites.models import Site
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.management import call_command
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
import urllib2
import base64

from cStringIO import StringIO
import csv, types
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
    
    lscraperrunevents = scraper.scraperrunevent_set.all().order_by("-run_started")[:1] 
    lastscraperrunevent = lscraperrunevents and lscraperrunevents[0] or None

    context = {
        'scraper_tags': scraper_tags,
        'selected_tab': 'overview',
        'scraper': scraper,
        'lastscraperrunevent':lastscraperrunevent,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        'scraper_contributors': scraper_contributors,
        'scraper_requesters': scraper_requesters,
        'related_views': related_views,
        'schedule_options': models.SCHEDULE_OPTIONS,
        }
    
    #get data for this scaper in a way that we can see exactly what is being transferred
    column_order = scraper.get_metadata('data_columns')
    if not user_owns_it:
        private_columns = scraper.get_metadata('private_columns')
    else:
        private_columns = None
    data = models.Scraper.objects.data_summary(scraper_id=scraper.guid,
                                               limit=50, 
                                               column_order=column_order,
                                               private_columns=private_columns)
    if len(data['rows']) > 12:
        data['morerows'] = data['rows'][9:]
        data['rows'] = data['rows'][:9]
    
    if data['rows']:
        context['datasinglerow'] = zip(data['headings'], data['rows'][0])
    
    context['data'] = data
    
    #if user.username == 'Julian_Todd':
    #    return render_to_response('codewiki/scraper_overview_jgt.html', context, context_instance=RequestContext(request))
    return render_to_response('codewiki/scraper_overview.html', context, context_instance=RequestContext(request))


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
                view.tags = request.POST.get('value', '')                                                  
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
                scraper.tags = request.POST.get('value', '')                                                  
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
        call_command('run_scrapers', short_name=short_name)
    
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

def scraper_screenshoot_scraper(request, wiki_type, short_name):
    if wiki_type == 'scraper':
        code_object = get_code_object_or_none(models.Scraper, short_name=short_name)
        if not code_object:
            return code_error_response(models.Scraper, short_name=short_name, request=request)
    else:
        code_object = get_code_object_or_none(models.View, short_name=short_name)
        if not code_object:
            return code_error_response(models.View, short_name=short_name, request=request)

    if not request.user.is_staff:
        raise Http404

    if request.POST.get('screenshoot_scraper', None) == '1':
        call_command('take_screenshot', short_name=short_name, domain=settings.VIEW_DOMAIN, verbose=False)
    
    return HttpResponseRedirect(reverse('code_overview', args=[code_object.wiki_type, short_name]))


def scraper_delete_scraper(request, wiki_type, short_name):
    if wiki_type == 'scraper':
        code_object = get_code_object_or_none(models.Scraper, short_name=short_name)
        if not code_object:
            return code_error_response(models.Scraper, short_name=short_name, request=request)
    else:
        code_object = get_code_object_or_none(models.View, short_name=short_name)
        if not code_object:
            return code_error_response(models.View, short_name=short_name, request=request)

    if code_object.owner() != request.user:
        raise Http404

    if request.POST.get('delete_scraper', None) == '1':
        code_object.deleted = True
        code_object.save()
        request.notifications.add("Your %s has been deleted" % wiki_type)
        return HttpResponseRedirect('/')

    return HttpResponseRedirect(reverse('code_overview', args=[code_object.wiki_type, short_name]))


def view_overview (request, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.View, short_name=short_name)
    if not scraper:
        return code_error_response(models.View, short_name=short_name, request=request)

    scraper_tags = Tag.objects.get_for_object(scraper)
    user_owns_it = (scraper.owner() == user)
    
    #get scrapers used in this view
    related_scrapers = scraper.relations.filter(wiki_type='scraper')
    
    context = {'selected_tab': 'overview', 'scraper': scraper, 'scraper_tags': scraper_tags, 'related_scrapers': related_scrapers, 'user_owns_it': user_owns_it}
    return render_to_response('codewiki/view_overview.html', context, context_instance=RequestContext(request))
    
    
def view_fullscreen (request, short_name):
    user = request.user
    urlquerystring = request.META["QUERY_STRING"]

    scraper = get_code_object_or_none(models.View, short_name=short_name)
    if not scraper:
        return code_error_response(models.View, short_name=short_name, request=request)

    return render_to_response('codewiki/view_fullscreen.html', {'scraper': scraper, 'urlquerystring':urlquerystring}, context_instance=RequestContext(request))

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
    
    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

    dictionary = { 'selected_tab': 'history', 'scraper': scraper, "user":user }
    
    itemlog = [ ]
    
    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    for commitentry in mercurialinterface.getcommitlog(scraper):
        try:    user = User.objects.get(pk=int(commitentry["userid"]))
        except: user = None
        
        item = {"type":"commit", "rev":commitentry['rev'], "datetime":commitentry["date"], "user":user}
        item['earliesteditor'] = commitentry['description'].split('|||')
        item["users"] = set([item["user"]])
        item["firstrev"] = item["rev"]
        item["firstdatetime"] = item["datetime"]
        item["revcount"] = 1
        itemlog.append(item)
    
    itemlog.reverse()
    
    # now obtain the run-events and zip together
    if scraper.wiki_type == 'scraper':
        runevents = scraper.scraper.scraperrunevent_set.all().order_by('run_started')
        for runevent in runevents:
            item = { "type":"runevent", "runevent":runevent, "datetime":runevent.run_started }
            if runevent.run_ended:
                runduration = runevent.run_ended - runevent.run_started
                item["runduration"] = runduration
                item["durationseconds"] = "%.0f" % (runduration.days*24*60*60 + runduration.seconds)
            item["runevents"] = [ runevent ]
            itemlog.append(item)
        
        itemlog.sort(key=lambda x: x["datetime"], reverse=True)
    
    # aggregate the history list
    aitemlog = [ ]
    previtem = None
    for item in itemlog:
        if previtem and item["type"] == "commit" and previtem["type"] == "commit" and \
                                        item["earliesteditor"] == previtem["earliesteditor"]:
            previtem["users"].add(item["user"])
            previtem["firstrev"] = item["rev"]
            previtem["firstdatetime"] = item["datetime"]
            previtem["revcount"] += 1
            timeduration = previtem["datetime"] - item["datetime"]
            previtem["durationminutes"] = "%.0f" % (timeduration.days*24*60 + timeduration.seconds/60.0)

        elif len(aitemlog) >= 3 and aitemlog[-2]["type"] == "runevent" and item["type"] == "runevent" and previtem["type"] == "runevent" and aitemlog[-3]["type"] == "runevent" and \
                        aitemlog[-2]["runevent"].run_ended and previtem["runevent"].run_ended and \
                        bool(previtem["runevent"].exception_message) == bool(aitemlog[-2]["runevent"].exception_message):
            aitemlog[-2]["runevents"].insert(0, previtem["runevent"])
            aitemlog[-2]["runduration"] += previtem["runduration"]
            runduration = aitemlog[-2]["runduration"] / len(aitemlog[-2]["runevents"])  # average
            aitemlog[-2]["durationseconds"] = "%.0f" % (runduration.days*24*60*60 + runduration.seconds)
            aitemlog[-1] = item
            previtem = item
            
        else:
            aitemlog.append(item)
            previtem = item
    
    dictionary["itemlog"] = aitemlog
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


    context = { 'selected_tab': 'history', 'scraper': scraper }

    # overcome lack of subtract in template
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        status["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]

    context["status"] = status
    context["code"] = status.get('code')
    
    # hack in link to user (was it a good idea to use userid rather than username?)
    try:    status["currcommit"]["user"] = User.objects.get(pk=int(status["currcommit"]["userid"]))
    except: pass
    try:    status["prevcommit"]["user"] = User.objects.get(pk=int(status["prevcommit"]["userid"]))
    except: pass
    try:    status["nextcommit"]["user"] = User.objects.get(pk=int(status["nextcommit"]["userid"]))
    except: pass

    context['error_messages'] = [ ]
    
    try: otherrev = int(request.GET.get('otherrev', '-1'))
    except ValueError: otherrev = None
    
    if otherrev != -1:
        try:
            reversion = mercurialinterface.getreversion(otherrev)
            context["othercode"] = reversion["text"].get(status['scraperfile'])
        except IndexError:
            context['error_messages'].append('Bad otherrev index')

    if context.get("othercode"):
        sqm = difflib.SequenceMatcher(None, context["code"].splitlines(), context["othercode"].splitlines())
        context['matcheropcodes'] = json.dumps(sqm.get_opcodes())
    
    return render_to_response('codewiki/code.html', context, context_instance=RequestContext(request))


def tags(request, wiki_type, short_name):
    if wiki_type == 'scraper':
        code_object = get_code_object_or_none(models.Scraper, short_name)
    else:
        code_object = get_code_object_or_none(models.View, short_name)
    return HttpResponse(", ".join([tag.name for tag in code_object.tags]))


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

def generate_csv(dictlist, offset, max_length=None):
    keyset = set()
    for row in dictlist:
        if "latlng" in row:   # split the latlng
            row["lat"], row["lng"] = row.pop("latlng") 
        row.pop("date_scraped", None) 
        keyset.update(row.keys())

    fout = StringIO()
    writer = csv.writer(fout, dialect='excel')
    truncated = False

    if offset == 0:
        writer.writerow([k.encode("utf-8") for k in keyset])
    for rowdict in dictlist:
        if max_length:
            # Save the length of the file in case adding
            # the next line takes it over the limit
            last_good_length = fout.tell()
            
        writer.writerow([stringnot(rowdict.get(key)) for key in keyset])

        if max_length and fout.tell() > max_length:
            fout.seek(last_good_length)
            truncated = True
            break

    result = fout.getvalue(True)
    fout.close()
    return result, truncated

def stream_csv(scraper, step=5000, max_rows=1000000):
    for offset in range(0, max_rows, step):
        dictlist = models.Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=step, offset=offset)
        
        yield generate_csv(dictlist, offset)[0]
        if len(dictlist) != step:
            break   #we've reached the end of the data


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

    row_limit = 5000

    truncated_message = 'THIS IS A SUBSET OF THE DATA ONLY. GOOGLE DOCS LIMITS FILES TO 1MB. DOWNLOAD THE FULL DATASET AS CSV HERE: %s\n' % str(csv_url)
    subset_message = 'THIS IS A SUBSET OF THE DATA ONLY. A MAXIMUM OF %s RECORDS CAN BE UPLOADED FROM SCRAPERWIKI. DOWNLOAD THE FULL DATASET AS CSV HERE: %s\n' % (str(row_limit), csv_url)
    
    max_length = settings.GDOCS_UPLOAD_MAX - max(len(truncated_message), len(subset_message))
    csv_data, truncated = generate_csv(models.Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=row_limit), 0, max_length)

    if truncated:
        title = title + ' [SUBSET ONLY]'
        csv_data = truncated_message.encode('utf-8') + csv_data
    elif scraper.record_count > row_limit:
        csv_data = subset_message.encode('utf-8') + csv_data

    #create client and authenticate
    client = gdata.docs.service.DocsService()
    client.ClientLogin(settings.GDOCS_UPLOAD_USER, settings.GDOCS_UPLOAD_PASSWORD)

    #create a document reference
    ms = gdata.MediaSource(file_handle=StringIO(csv_data), content_type=gdata.docs.service.SUPPORTED_FILETYPES['CSV'], content_length=len(csv_data))

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
    print scraper
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)
    print scraper

    user = request.user
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    # remove the user from follower list
    scraper.unfollow(user)
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)



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
                                         'languages': sorted([ ll[1] for ll in models.code.LANGUAGES ]), 
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


def convtounicode(text):
    try:   return unicode(text)
    except UnicodeDecodeError:  pass
        
    try:   return unicode(text, encoding='utf8')
    except UnicodeDecodeError:  pass
    
    try:   return unicode(text, encoding='latin1')
    except UnicodeDecodeError:  pass
        
    return unicode(text, errors='replace')


def proxycached(request):
    cacheid = request.POST.get('cacheid')
    
    # delete this later when no more need for debugging
    if not cacheid:  
        cacheid = request.GET.get('cacheid')
    
    if not cacheid:
        return HttpResponse(json.dumps({'message':"No cacheid found"}), mimetype="text/plain")
    
    fin = urllib2.urlopen(settings.HTTPPROXYURL + "/Page?" + cacheid)
    res = { 'type':fin.headers.type, 'url':fin.geturl(), 'cacheid':cacheid }
    if fin.headers.maintype == 'text':
        res['content'] = convtounicode(fin.read())
    else:
        res['content'] = base64.encodestring(fin.read())
        res['encoding'] = "base64"
        
    return HttpResponse(json.dumps(res), mimetype="text/plain")



#save a code object
def save_code(code_object, user, code_text, earliesteditor, commitmessage, sourcescraper = ''):

    code_object.line_count = int(code_text.count("\n"))
    
    # perhaps the base class should call the upper class updates, not the other way round
    if code_object.wiki_type == "scraper":
        code_object.save()  # save the object using the base class (otherwise causes a major failure if it doesn't exist)
        code_object.scraper.update_meta()
        code_object.scraper.save()
    else:
        code_object.update_meta()
        code_object.save()

        #make link to source scraper
        if sourcescraper:
            scraper = get_code_object_or_none(models.Code, short_name=sourcescraper)
            if scraper:
                code_object.relations.add(scraper)

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
    sourcescraper = session_scraper_draft.get('sourcescraper')
    commitmessage = session_scraper_draft.get('commit_message', "") # needed?
    earliesteditor = session_scraper_draft.get('earliesteditor', "") #needed?
    save_code(draft_scraper, request.user, draft_code, earliesteditor, commitmessage, sourcescraper)

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
    commitmessage = request.POST.get('commit_message', "")
    sourcescraper = request.POST.get('sourcescraper', "")    
    
    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        earliesteditor = request.POST.get('earliesteditor', "")
        save_code(scraper, request.user, code, earliesteditor, commitmessage, sourcescraper)  

        # Work out the URL to return in the JSON object
        url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name':scraper.short_name})
        if action.startswith("commit"):
            response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})

        # Build the JSON object and return it
        res = json.dumps({'redirect':'true', 'url':response_url,})
        return HttpResponse(res)

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'commit_message': request.POST.get('commit_message'), 'sourcescraper': sourcescraper}
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
    return_url = reverse('frontpage')
    language = language.lower()
    
    codemirrorversion = request.GET.get('codemirrorversion', '')
    if not re.match('[\d\.]+$', codemirrorversion):
        codemirrorversion = settings.CODEMIRROR_VERSION

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

    #if a source scraper has been set, then pass it to the page
    source_scraper = ''
    if scraper.wiki_type == 'view' and request.GET.get('sourcescraper', False):
       source_scraper =  request.GET.get('sourcescraper', False)

    context = {}
    context['form'] = form
    context['scraper'] = scraper
    context['has_draft'] = has_draft
    context['user'] = request.user
    context['source_scraper'] = source_scraper
    context['quick_help_template'] = 'codewiki/includes/%s_quick_help_%s.html' % (scraper.wiki_type, scraper.language.lower())
    context['selected_tab'] = 'code'
    context['codemirrorversion'] = codemirrorversion
    
    return render_to_response('codewiki/editor.html', context, context_instance=RequestContext(request))

