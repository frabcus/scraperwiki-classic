from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.contrib.auth.models import User
from django.views.decorators.http import condition
import textile
from django.conf import settings

from managers.datastore import DataStore
from codewiki import models
import frontend

import urllib
import re
import urllib2
import base64
import datetime

try:                import json
except ImportError: import simplejson as json


def listolddatastore(request):
    dataproxy = DataStore("", "")
    rc, arg = dataproxy.request(('listolddatastore',))
    #scrapers = models.Code.objects.filter(wiki_type="scraper")
    scrapers = [ ]
    for lguid in arg:
        if lguid[0]:
            lscraper = models.Code.objects.filter(guid=lguid[0])
            if lscraper:
                scrapers.append(lscraper[0])
    
    res = [ ]
    for scraper in scrapers:
        res.append('<a href="%s">%s</a>' % (reverse('code_overview', args=[scraper.wiki_type, scraper.short_name]), scraper.short_name))
    return HttpResponse("<ul><li>%s</li></ul>" % ("</li><li>".join(res)))


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
    try:
        scraper = models.Code.unfiltered.get(short_name=short_name)
    except models.Code.DoesNotExist:
        raise Http404
    if not scraper.actionauthorized(request.user, action):
        raise Http404
        
    # extra post conditions to make spoofing these calls a bit of a hassle
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
                item["runduration"] = runevent.getduration()
                item["durationseconds"] = runevent.getdurationseconds()
            item["groupkey"] = "runevent"
            if runevent.exception_message:
                item["groupkey"] += "|||" + str(runevent.exception_message.encode('utf-8'))
            if runevent.pid != -1:
                item["groupkey"] += "|||" + str(runevent.pid)
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
    context["related_views"] = models.View.objects.filter(relations=scraper)
    
    # XXX to be deprecated when old style datastore is abolished
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
    
    # this is the only one to call.  would like to know the exception that's expected
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
            ckanparams = {"name": scraper.short_name,
                          "title": scraper.title.encode('utf-8'),
                          "url": settings.MAIN_URL+reverse('code_overview', args=[scraper.wiki_type, short_name])}
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
        scraper.save() # XXX need to save so template render gets new values, bad that it saves below also!
        response_text = render_to_string('codewiki/includes/run_interval.html', {'scraper': scraper}, context_instance=RequestContext(request))

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


# these ought to be done javascript from the page to fill in the ajax input box
def tags(request, wiki_type, short_name):
    scraper = getscraperor404(request, short_name, "gettags")
    return HttpResponse(", ".join([tag.name  for tag in scraper.gettags()]))

def raw_about_markup(request, wiki_type, short_name):
    scraper = getscraperor404(request, short_name, "getdescription")
    return HttpResponse(scraper.description, mimetype='text/x-web-textile')





def follow(request, short_name):
    scraper = getscraperor404(request, short_name, "setfollow")
    scraper.add_user_role(request.user, 'follow')
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)

def unfollow(request, short_name):
    scraper = getscraperor404(request, short_name, "setfollow")
    scraper.unfollow(request.user)
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
    request.notifications.used = True   # Remove any pending notifications, i.e. the "don't worry, your scraper is safe" one
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


def export_csv(request, short_name):
    tablename = request.GET.get('tablename', "swdata")
    query = "select * from `%s`" % tablename
    qsdata = { "name":short_name.encode('utf-8'), "query":query.encode('utf-8'), "format":"csv" }
    return HttpResponseRedirect("%s?%s" % (reverse("api:method_sqlite"), urllib.urlencode(qsdata)))


    # could be replaced with the dataproxy chunking technology now available in there,
    # but as it's done, leave it here
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

# see http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
@condition(etag_func=None)
def export_sqlite(request, short_name):
    scraper = getscraperor404(request, short_name, "exportsqlite")
    
    dataproxy = DataStore(scraper.guid, scraper.short_name)
    initsqlitedata = dataproxy.request(("sqlitecommand", "downloadsqlitefile", 0, 0))
    if "filesize" not in initsqlitedata:
        return HttpResponse(str(initsqlitedata), mimetype="text/plain")
    
    response = HttpResponse(stream_sqlite(dataproxy, initsqlitedata["filesize"]), mimetype='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s.sqlite' % (short_name)
    response["Content-Length"] = initsqlitedata["filesize"]
    return response
