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
import urllib

from managers.datastore import DataStore

from codewiki import models
from api.emitters import CSVEmitter 
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
    except Exception, e:
        print e, type(e)
        return None

def code_error_response(klass, short_name, request):
    if klass.unfiltered.filter(short_name=short_name, deleted=True).count() == 1:
        body = 'Sorry, this %s has been deleted by the owner' % klass.__name__
        string = render_to_string('404.html', {'heading': 'Deleted', 'body': body}, context_instance=RequestContext(request))
        return HttpResponseNotFound(string)
    else:
        raise Http404


def getscraperorresponse(request, wiki_type, short_name, rdirect, action):
    try:
        scraper = models.Code.unfiltered.get(short_name=short_name)
    except models.Code.DoesNotExist:
        message =  "Sorry, this %s does not exist" % wiki_type
        return HttpResponseNotFound(render_to_string('404.html', {'heading':'Not found', 'body':message}, context_instance=RequestContext(request)))
    
    if wiki_type != scraper.wiki_type:
        return HttpResponseRedirect(reverse(rdirect, args=[scraper.wiki_type, short_name]))
        
    if not scraper.actionauthorized(request.user, action):
        return HttpResponseNotFound(render_to_string('404.html', scraper.authorizationfailedmessage(request.user, action), context_instance=RequestContext(request)))
    return scraper


def getscraperor404(request, short_name, action):
    scraper = models.Code.unfiltered.get(short_name=short_name)
    if not scraper.actionauthorized(request.user, action):
        raise Http404
        
    if action == "changeadmin":
        if not (request.method == 'POST' and request.is_ajax()):
            raise Http404
    if action == "converttosqlitedatastore":
        if request.POST.get('converttosqlitedatastore', None) != 'converttosqlitedatastore':
            raise Http404
    
    if action in ["delete_data", "schedule_scraper", "run_scraper", "screenshoot_scraper", "delete_scraper"]:
        if request.POST.get(action, None) != '1':
            raise Http404
        
    return scraper


def comments(request, wiki_type, short_name):
    scraper = getscraperorresponse(request, wiki_type, short_name, "scraper_comments", "comments")
    if isinstance(scraper, HttpResponse):  return scraper
    
    context = {'selected_tab':'comments', 'scraper':scraper }
    context["scraper_tags"] = scraper.gettags()
    context["user_owns_it"] = (scraper.owner() == request.user)
    context["user_follows_it"] = (request.user in scraper.followers())
    context["scraper_contributors"] = scraper.contributors()
    context["scraper_owner"] = scraper.owner()    
    context["scraper_followers"] = scraper.followers()    
    
    return render_to_response('codewiki/comments.html', context, context_instance=RequestContext(request))


def scraper_history(request, wiki_type, short_name):
    scraper = getscraperorresponse(request, wiki_type, short_name, "scraper_history", "history")
    if isinstance(scraper, HttpResponse):  return scraper
    
    context = { 'selected_tab': 'history', 'scraper': scraper, "user":request.user }
    
    itemlog = [ ]
    for commitentry in scraper.get_commit_log():
        item = { "type":"commit", "rev":commitentry['rev'], "datetime":commitentry["date"] }
        if "user" in commitentry:
            item["user"] = commitentry["user"]
        item['earliesteditor'] = commitentry['description'].split('|||')
        if itemlog:
            item["prevrev"] = itemlog[-1]["rev"]
        item["groupkey"] = "commit|||"+ str(item['earliesteditor'])
        itemlog.append(item)
    itemlog.reverse()
    
    # now obtain the run-events and sort together
    if scraper.wiki_type == 'scraper':
        runevents = scraper.scraper.scraperrunevent_set.all().order_by('run_started')
        for runevent in runevents:
            item = { "type":"runevent", "runevent":runevent, "datetime":runevent.run_started }
            if runevent.run_ended:
                runduration = runevent.run_ended - runevent.run_started
                item["runduration"] = runduration
                item["durationseconds"] = "%.0f" % (runduration.days*24*60*60 + runduration.seconds)
            if runevent.exception_message:
                item["groupkey"] = "runevent|||" + str(runevent.exception_message.encode('utf-8'))
            else:
                item["groupkey"] = "runevent|||"
            itemlog.append(item)
        
        itemlog.sort(key=lambda x: x["datetime"], reverse=True)
    
    context["itemlog"] = itemlog
    context["filestatus"] = scraper.get_file_status()
    
    return render_to_response('codewiki/history.html', context, context_instance=RequestContext(request))




def code_overview(request, wiki_type, short_name):
    scraper = getscraperorresponse(request, wiki_type, short_name, "code_overview", "overview")
    if isinstance(scraper, HttpResponse):  return scraper
        
    context = {'selected_tab':'overview', 'scraper':scraper }
    context["scraper_tags"] = scraper.gettags()
    context["user_owns_it"] = (scraper.owner() == request.user)
    
    if wiki_type == 'view':
        context["related_scrapers"] = scraper.relations.filter(wiki_type='scraper')
        if scraper.language == 'html':
            code = scraper.saved_code()
            if re.match('<div\s+class="inline">', code):
                context["htmlcode"] = code
        return render_to_response('codewiki/view_overview.html', context, context_instance=RequestContext(request))

    # else section
    assert wiki_type == 'scraper'

    context["schedule_options"] = models.SCHEDULE_OPTIONS
    context["license_choices"] = models.LICENSE_CHOICES
    
    context["user_follows_it"] = (request.user in scraper.followers())
    context["scraper_contributors"] = scraper.contributors()
    context["scraper_requesters"] = scraper.requesters()    
    
    context["related_views"] = models.View.objects.filter(relations=scraper)
    
    lscraperrunevents = scraper.scraper.scraperrunevent_set.all().order_by("-run_started")[:1] 
    context["lastscraperrunevent"] = lscraperrunevents and lscraperrunevents[0] or None

            # to be deprecated when old style datastore is abolished
    column_order = scraper.get_metadata('data_columns')
    if not context["user_owns_it"]:
        private_columns = scraper.get_metadata('private_columns')
    else:
        private_columns = None
    try:
        data = models.Scraper.objects.data_summary(scraper_id=scraper.guid,
                                                   limit=50, 
                                                   column_order=column_order,
                                                   private_columns=private_columns)
    except:
        data = {'rows': []}

    
    if len(data['rows']) > 12:
        data['morerows'] = data['rows'][9:]
        data['rows'] = data['rows'][:9]
    
    if data['rows']:
        context['datasinglerow'] = zip(data['headings'], data['rows'][0])
    context['data'] = data
    
    try:
        dataproxy = DataStore(scraper.guid, scraper.short_name)
        sqlitedata = dataproxy.request(("sqlitecommand", "datasummary", None, None))
        if sqlitedata and type(sqlitedata) not in [str, unicode]:
            context['sqlitedata'] = sqlitedata["tables"]
    except:
        pass
    
    # put in ckan connections
    if request.user.is_staff:
        try:
            dataproxy.request(("sqlitecommand", "attach", "ckan_datastore", "src"))
            ckansqlite = "select src.records.ckan_url, src.records.notes from src.resources left join src.records on src.records.id=src.resources.records_id  where src.resources.scraperwiki=?"
            lsqlitedata = dataproxy.request(("sqlitecommand", "execute", ckansqlite, (scraper.short_name,)))
            if lsqlitedata.get("data"):
                context['ckanresource'] = dict(zip(lsqlitedata["keys"], lsqlitedata["data"][0]))
        except:
            pass
            
        if context.get('sqlitedata') and "ckanresource" not in context:
            ckanparams = {"name":scraper.short_name, "title":scraper.title, "url":settings.MAIN_URL+reverse('code_overview', args=[scraper.wiki_type, short_name])}
            ckanparams["resources_url"] = settings.MAIN_URL+reverse('export_sqlite', args=[scraper.short_name])
            ckanparams["resources_format"] = "Sqlite"
            ckanparams["resources_description"] = "Scraped data"
            context["ckansubmit"] = "http://ckan.net/package/new?%s" % urllib.urlencode(ckanparams)

    return render_to_response('codewiki/scraper_overview.html', context, context_instance=RequestContext(request))


# all remaining functions are ajax or temporary pages linked only 
# through the site, so throwing 404s is adequate

def view_admin(request, short_name):
    scraper = getscraperor404(request, short_name, "changeadmin")
    view = scraper.view

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
        view.settags(request.POST.get('value', ''))  # splitting is in the library
        response_text = ", ".join([tag.name for tag in view.gettags()])

    view.save()
    response.write(response_text)
    return response
    
    
def scraper_admin(request, short_name):
    scraper = getscraperor404(request, short_name, "changeadmin")
    scraper = scraper.scraper
    
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
        scraper.settags(request.POST.get('value', ''))
        response_text = ", ".join([tag.name for tag in scraper.gettags()])

    if element_id == 'spnRunInterval':
        scraper.run_interval = int(request.POST.get('value', None))
        response_text = models.SCHEDULE_OPTIONS_DICT[scraper.run_interval]

    if element_id == 'spnLicenseChoice':
        scraper.license = request.POST.get('value', None)
        response_text = scraper.license

    if element_id == 'publishScraperButton':
        scraper.published = True

    scraper.save()
    response.write(response_text)
    return response


def scraper_delete_data(request, short_name):
    scraper = getscraperor404(request, short_name, "delete_data")
    dataproxy = DataStore(scraper.guid, scraper.short_name)
    dataproxy.request(("clear_datastore",))
    if scraper.wiki_type == "scraper":
        scraper.scraper.scrapermetadata_set.all().delete()
        scraper.scraper.update_meta()
    scraper.save()
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

def scraper_converttosqlitedatastore(request, short_name):
    scraper = getscraperor404(request, short_name, "converttosqlite")
    dataproxy = DataStore(scraper.guid, scraper.short_name)
    dataproxy.request(("converttosqlitedatastore",))
    if scraper.wiki_type == "scraper":
        scraper.scraper.update_meta()
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

def scraper_schedule_scraper(request, short_name):
    scraper = getscraperor404(request, short_name, "schedulescraper")
    if scraper.wiki_type == "scraper":
        scraper.scraper.last_run = None
        scraper.scraper.save()
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

def scraper_run_scraper(request, short_name):
    scraper = getscraperor404(request, short_name, "run_scraper")
    if scraper.wiki_type == "scraper":
        scraper.scraper.last_run = None
        scraper.scraper.save()
        call_command('run_scrapers', short_name=short_name)
    return HttpResponseRedirect(reverse('code_overview', args=[scraper.wiki_type, short_name]))

def scraper_screenshoot_scraper(request, wiki_type, short_name):
    scraper = getscraperor404(request, short_name, "screenshoot_scraper")
    call_command('take_screenshot', short_name=short_name, domain=settings.VIEW_DOMAIN, verbose=False)
    return HttpResponseRedirect(reverse('code_overview', args=[code_object.wiki_type, short_name]))

def scraper_delete_scraper(request, wiki_type, short_name):
    scraper = getscraperor404(request, short_name, "delete_scraper")
    scraper.deleted = True
    scraper.save()
    request.notifications.add("Your %s has been deleted" % wiki_type)
    return HttpResponseRedirect('/')



# this ought to be done javascript from the page to fill in the ajax input box
def tags(request, wiki_type, short_name):
    scraper = models.Code.unfiltered.get(short_name=short_name)
    return HttpResponse(", ".join([tag.name  for tag in scraper.gettags()]))


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
            try:
                row["lat"], row["lng"] = row.pop("latlng") 
            except:
                row["lat"], row["lng"] = ("", "")
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
        dictlist = models.Scraper.objects.data_dictlist(scraper_id=scraper.guid, short_name=scraper.short_name, tablename="", limit=step, offset=offset)
        
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

            
def stream_sqlite(dataproxy, filesize, memblock=100000):
    for offset in range(0, filesize, memblock):
        sqlitedata = dataproxy.request(("sqlitecommand", "downloadsqlitefile", offset, memblock))
        content = sqlitedata.get("content")
        if sqlitedata.get("encoding") == "base64":
            content = base64.decodestring(content)
        yield content
        assert len(content) == sqlitedata.get("length"), len(content)
        if sqlitedata.get("length") < memblock:
            break

@condition(etag_func=None)
def export_sqlite(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)
    
    dataproxy = DataStore(scraper.guid, scraper.short_name)
    initsqlitedata = dataproxy.request(("sqlitecommand", "downloadsqlitefile", 0, 0))
    if "filesize" not in initsqlitedata:
        return HttpResponse(str(initsqlitedata), mimetype="text/plain")
    
    response = HttpResponse(stream_sqlite(dataproxy, initsqlitedata["filesize"]), mimetype='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s.sqlite' % (short_name)
    response["Content-Length"] = initsqlitedata["filesize"]
    return response


def sqlitequery(request):
    dataproxy = DataStore("sqlviewquery", "")  # zero length short name means it will open up a :memory: database
    for aattach in request.GET.get('attach', '').split(";"):
        if aattach:
            aa = aattach.split(",")
            sqlitedata = dataproxy.request(("sqlitecommand", "attach", aa[0], (len(aa) == 2 and aa[1] or None)))
    
    sqlquery = request.GET.get('query')
    if not sqlquery:
        return HttpResponse("Example:  ?attach=scraper_name,src&query=select+*+from+src.swdata+limit+10")
    
    sqlitedata = dataproxy.request(("sqlitecommand", "execute", sqlquery, None))
    #return HttpResponse(json.dumps(sqlitedata), mimetype="application/json")
    return HttpResponse(json.dumps(sqlitedata), mimetype="text/plain")














def follow(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)

    user_owns_it = (scraper.owner() == request.user)
    user_follows_it = (request.user in scraper.followers())
    # add the user to follower list
    scraper.add_user_role(request.user, 'follow')
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)


def unfollow(request, short_name):
    scraper = get_code_object_or_none(models.Scraper, short_name=short_name)
    print scraper
    if not scraper:
        return code_error_response(models.Scraper, short_name=short_name, request=request)
    print scraper

    user_owns_it = (scraper.owner() == request.user)
    user_follows_it = (request.user in scraper.followers())
    # remove the user from follower list
    scraper.unfollow(request.user)
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)



def choose_template(request, wiki_type):
    context = { "wiki_type":wiki_type }
    context["templates"] = models.Code.objects.filter(isstartup=True, wiki_type=wiki_type).order_by('language')
    context["sourcescraper"] = request.GET.get('sourcescraper', '')
    
    if request.GET.get('ajax'):
        template = 'codewiki/includes/choose_template.html'
    else:
        template = 'codewiki/choose_template.html'
    
    if wiki_type == "scraper":
        context["languages"] = models.code.SCRAPER_LANGUAGES
    else:
        context["languages"] = models.code.VIEW_LANGUAGES
    
    return render_to_response(template, context, context_instance=RequestContext(request))


    
def delete_draft(request):
    if request.session.get('ScraperDraft', False):
        del request.session['ScraperDraft']

    # Remove any pending notifications, i.e. the "don't worry, your scraper is safe" one
    request.notifications.used = True

    return HttpResponseRedirect(reverse('frontpage'))


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
        return HttpResponse(json.dumps({'type':'error', 'content':"No cacheid found"}), mimetype="application/json")
    
    proxyurl = settings.HTTPPROXYURL + "/Page?" + cacheid
    result = { 'proxyurl':proxyurl, 'cacheid':cacheid }
    try:
        fin = urllib2.urlopen(proxyurl)
        result["mimetype"] = fin.headers.type
        if fin.headers.maintype == 'text' or fin.headers.type == "application/json":
            result['content'] = convtounicode(fin.read())
        else:
            result['content'] = base64.encodestring(fin.read())
            result['encoding'] = "base64"
    except urllib2.URLError, e: 
        result['type'] = 'exception'
        result['content'] = str(e)
    
    return HttpResponse(json.dumps(result), mimetype="application/json")



