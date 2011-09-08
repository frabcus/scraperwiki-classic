from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.core.exceptions import PermissionDenied, SuspiciousOperation
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
import socket



try:                import json
except ImportError: import simplejson as json

PRIVACY_STATUSES_UI = [ ('public', 'can be edited by anyone who is logged on'),
                        ('visible', 'can only be edited by those listed as editors'), 
                        ('private', 'cannot be seen by anyone except for the designated editors'), 
                        ('deleted', 'is deleted') 
                      ]


def getscraperorresponse(request, wiki_type, short_name, rdirect, action):
    if action in ["delete_scraper", "delete_data"]:
        if not (request.method == 'POST' and request.POST.get(action, None) == '1'):
            raise SuspiciousOperation # not the best description of error, but best available, see comment on getscraperor404 below
    
    try:
        scraper = models.Code.objects.get(short_name=short_name)
    except models.Code.DoesNotExist:
        message =  "Sorry, that %s doesn't seem to exist" % wiki_type
        heading = "404: File not found"
        return HttpResponseNotFound(render_to_string('404.html', {'heading':heading, 'body':message}, context_instance=RequestContext(request)))
    
    if rdirect and wiki_type != scraper.wiki_type:
        return HttpResponseRedirect(reverse(rdirect, args=[scraper.wiki_type, short_name]))
        
    if not scraper.actionauthorized(request.user, action):
        return HttpResponseNotFound(render_to_string('404.html', scraper.authorizationfailedmessage(request.user, action), context_instance=RequestContext(request)))
    return scraper


# XXX This should not throw 404s for malformed request or lack of permissions, but 
# unfortunately Django has no such built in exceptions. Could hand roll our own like this:
#   http://theglenbot.com/creating-a-custom-http403-exception-in-django/
# Am using PermissionDenied and SuspiciousOperation as partial workaround meanwhile, see:
#   http://groups.google.com/group/django-users/browse_thread/thread/8d3dda89858ff2ee
def getscraperor404(request, short_name, action):
    try:
        scraper = models.Code.objects.get(short_name=short_name)
    except models.Code.DoesNotExist:
        raise Http404
    
    if not scraper.actionauthorized(request.user, action):
        raise PermissionDenied
        
    # extra post conditions to make spoofing these calls a bit of a hassle
    if action in ["changeadmin", "settags", "set_privacy_status"]:
        if not (request.method == 'POST' and request.is_ajax()):
            raise SuspiciousOperation
    
    if action in ["schedule_scraper", "run_scraper", ]:
        if request.POST.get(action, None) != '1':
            raise SuspiciousOperation
        
    return scraper


def comments(request, wiki_type, short_name):
    scraper = getscraperorresponse(request, wiki_type, short_name, "scraper_comments", "comments")
    if isinstance(scraper, HttpResponse):  return scraper
    context = {'selected_tab':'comments', 'scraper':scraper }
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
    context["userrolemap"] = scraper.userrolemap()
    
    # if {% if a in b %} worked we wouldn't need these two
    context["user_owns_it"] = (request.user in context["userrolemap"]["owner"])
    context["user_edits_it"] = (request.user in context["userrolemap"]["owner"]) or (request.user in context["userrolemap"]["editor"])
    
    context["PRIVACY_STATUSES"] = PRIVACY_STATUSES_UI[0:2]  
    if request.user.is_staff:
        context["PRIVACY_STATUSES"] = PRIVACY_STATUSES_UI[0:3]  
    context["privacy_status_name"] = dict(PRIVACY_STATUSES_UI).get(scraper.privacy_status)

    context["api_base"] = "%s/api/1.0/" % settings.API_URL
    
    # view tpe
    if wiki_type == 'view':
        context["related_scrapers"] = scraper.relations.filter(wiki_type='scraper')
        if scraper.language == 'html':
            code = scraper.saved_code()
            if re.match('<div\s+class="inline">', code):
                context["htmlcode"] = code
        return render_to_response('codewiki/view_overview.html', context, context_instance=RequestContext(request))

    #
    # (else) scraper type section
    #
    assert wiki_type == 'scraper'

    context["schedule_options"] = models.SCHEDULE_OPTIONS
    context["license_choices"] = models.LICENSE_CHOICES
    context["related_views"] = models.View.objects.filter(relations=scraper).exclude(privacy_status="deleted")

    previewsqltables = re.findall("(?s)__BEGINPREVIEWSQL__.*?\n(.*?)\n__ENDPREVIEWSQL__", scraper.description)
    previewrssfeeds = re.findall("(?s)__BEGINPREVIEWRSS__.*?\n(.*?)\n__ENDPREVIEWRSS__", scraper.description)
    
        # there's a good case for having this load through the api by ajax
        # instead of inlining it and slowing down the page load considerably
    dataproxy = None
    try:
        dataproxy = DataStore(scraper.short_name)
        sqlitedata = dataproxy.request({"maincommand":"sqlitecommand", "command":"datasummary", "limit":10})
        if not sqlitedata:
            context['sqliteconnectionerror'] = 'No content in response'
        elif type(sqlitedata) in [str, unicode]:
            context['sqliteconnectionerror'] = sqlitedata
        elif 'tables' not in sqlitedata:
            if 'status' in sqlitedata:
                if sqlitedata['status'] == 'No sqlite database':
                    pass # just leave 'sqlitedata' not in context
                else:
                    context['sqliteconnectionerror'] = sqlitedata['status']
            else:
                context['sqliteconnectionerror'] = 'Response with unexpected format'

            # success, have good data
        else:
            context['sqlitedata'] = [ ]
            for sqltablename, sqltabledata in sqlitedata['tables'].items():
                sqltabledata["tablename"] = sqltablename
                context['sqlitedata'].append(sqltabledata)

            try:
                beta_user = request.user.get_profile().beta_user
            except frontend.models.UserProfile.DoesNotExist:
                beta_user = False
            except AttributeError:  # happens with AnonymousUser which has no get_profile function!
                beta_user = False
                
            # add in the user defined sql tables.  
            # the hazard is if you put in a very large request then it will time out before 
            # your page gets generated, so we must protect against this type of thing
            if beta_user:
                for utabnum, previewsqltable in reversed(list(enumerate(previewsqltables))):
                    lsqlitedata = dataproxy.request({"maincommand":"sqliteexecute", "sqlquery":previewsqltable, "data":[]})
                    if "keys" in lsqlitedata:   # otherwise 'error' is in the result
                        context['sqlitedata'].insert(0, {"tablename":"user_defined_%d"%(utabnum+1), "keys":lsqlitedata["keys"], "rows":lsqlitedata["data"], "sql":previewsqltable})

    except socket.error, e:
        context['sqliteconnectionerror'] = e.args[1]  # 'Connection refused'

        
    # unfinished CKAN integration
    if False and dataproxy and request.user.is_staff:
        try:
            dataproxy.request({"maincommand":"sqlitecommand", "command":"attach", "name":"ckan_datastore", "asname":"src"})
            ckansqlite = "select src.records.ckan_url, src.records.notes from src.resources left join src.records on src.records.id=src.resources.records_id  where src.resources.scraperwiki=?"
            attachlist = [{"name":"ckan_datastore", "asname":"src"}]
            lsqlitedata = dataproxy.request({"maincommand":"sqliteexecute", "sqlquery":ckansqlite, "data":(scraper.short_name,), "attachlist":attachlist})
        except socket.error, e:
            lsqlitedata = None

        if lsqlitedata:
            if lsqlitedata.get("data"):
                context['ckanresource'] = dict(zip(lsqlitedata["keys"], lsqlitedata["data"][0]))
                
            if context.get('sqlitedata') and "ckanresource" not in context:
                ckanparams = {"name": scraper.short_name,
                              "title": scraper.title.encode('utf-8'),
                              "url": settings.MAIN_URL+reverse('code_overview', args=[scraper.wiki_type, short_name])}
                ckanparams["resources_url"] = settings.MAIN_URL+reverse('export_sqlite', args=[scraper.short_name])
                ckanparams["resources_format"] = "Sqlite"
                ckanparams["resources_description"] = "Scraped data"
                context["ckansubmit"] = "http://ckan.net/package/new?%s" % urllib.urlencode(ckanparams)

    if dataproxy:
        dataproxy.close()

    return render_to_response('codewiki/scraper_overview.html', context, context_instance=RequestContext(request))


# all remaining functions are ajax or temporary pages linked only 
# through the site, so throwing 404s is adequate

def scraper_admin_settags(request, short_name):
    scraper = getscraperor404(request, short_name, "settags")
    scraper.settags(request.POST.get('value', ''))  # splitting is in the library
    return render_to_response('codewiki/includes/tagslist.html', { "scraper_tags":scraper.gettags() })

def scraper_admin_privacystatus(request, short_name):
    scraper = getscraperor404(request, short_name, "set_privacy_status")
    scraper.privacy_status = request.POST.get('value', '')
    scraper.save()
    return HttpResponse(dict(PRIVACY_STATUSES_UI)[scraper.privacy_status])

def scraper_admin_controleditors(request, short_name):
    username  = request.GET.get('roleuser', '')
    newrole   = request.GET.get('newrole', '')    
    processed = False

    if not username:
        return HttpResponse("Failed: username not provided")
        
    try:
        roleuser = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("Failed: username '%s' not found" % username)
    
    # We allow '' for removing a role
    if newrole not in ['editor', 'follow', '']:
        return HttpResponse("Failed: role '%s' unrecognized" % newrole)

    if newrole == '':
        # Make sure we are either removing the role from ourselves or have permission
        # to remove it from another user
        if request.user.id == roleuser.id:
            scraper = getscraperor404(request, short_name, "remove_self_editor")
        else:
            scraper = getscraperor404(request, short_name, "set_controleditors")
        
        # If the user is an owner and is trying to remove their own role then we 
        # should disregard this request as they cannot remove that role
        if models.UserCodeRole.objects.filter(code=scraper, user=roleuser, role='owner').count():
            return HttpResponse("Failed: You cannot remove yourself as owner" )                
        scraper.set_user_role(roleuser, 'editor', remove=True)
        context = { "role":'', "contributor":request.user }        
        processed = True        
    else:
        scraper = getscraperor404(request, short_name, "set_controleditors")

    if not processed:    
        if models.UserCodeRole.objects.filter(code=scraper, user=roleuser, role=newrole):
            return HttpResponse("Warning: user is already '%s'" % newrole)
    
        if models.UserCodeRole.objects.filter(code=scraper, user=roleuser, role='owner'):
            return HttpResponse("Failed: user is already owner")
        
        newuserrole = scraper.set_user_role(roleuser, newrole)
        context = { "role":newuserrole.role, "contributor":newuserrole.user }
        processed = True
        
    context["user_owns_it"] = (request.user in scraper.userrolemap()["owner"])
    if processed:
        return render_to_response('codewiki/includes/contributor.html', context, context_instance=RequestContext(request))
    return HttpResponse("Failed: unknown")



def view_admin(request, short_name):
    scraper = getscraperor404(request, short_name, "changeadmin")
    view = scraper.view

    response = HttpResponse()
    response_text = ''
    element_id = request.POST.get('id', None)
    if element_id == 'divAboutScraper':
        view.set_docs(request.POST.get('value', None), request.user)
        response_text = textile.textile(view.description)

    if element_id == 'hCodeTitle':
        view.title = request.POST.get('value', None)
        response_text = view.title

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
        scraper.set_docs(request.POST.get('value', None), request.user)
        response_text = textile.textile(scraper.description)
        
    if element_id == 'hCodeTitle':
        scraper.title = request.POST.get('value', None)
        response_text = scraper.title

    if element_id == 'spnRunInterval':
        scraper.run_interval = int(request.POST.get('value', None))
        scraper.save() # XXX need to save so template render gets new values, bad that it saves below also!
        context = {'scraper': scraper}
        context["user_owns_it"] = (request.user in scraper.userrolemap()["owner"])
        response_text = render_to_string('codewiki/includes/run_interval.html', context, context_instance=RequestContext(request))

    if element_id == 'spnLicenseChoice':
        scraper.license = request.POST.get('value', None)
        response_text = scraper.license

    scraper.save()
    response.write(response_text)
    return response


def scraper_delete_data(request, short_name):
    scraper = getscraperorresponse(request, "scraper", short_name, None, "delete_data")
    if isinstance(scraper, HttpResponse):  return scraper
    dataproxy = DataStore(scraper.short_name)
    dataproxy.request({"maincommand":"clear_datastore"})
    scraper.scraper.update_meta()
    scraper.save()
    request.notifications.add("Your data has been deleted")
    
    dataproxy.close()
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

def scraper_delete_scraper(request, wiki_type, short_name):
    scraper = getscraperorresponse(request, wiki_type, short_name, None, "delete_scraper")
    if isinstance(scraper, HttpResponse):  return scraper
    scraper.privacy_status = "deleted"
    scraper.save()
    request.notifications.add("Your %s has been deleted" % wiki_type)
    return HttpResponseRedirect(reverse('dashboard'))




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
    from httplib import BadStatusLine
    
    cacheid = request.POST.get('cacheid', None)
    
    # delete this later when no more need for debugging
    if not cacheid:   
        cacheid = request.GET.get('cacheid', None)
    
    if not cacheid:
        return HttpResponse(json.dumps({'type':'error', 'content':"No cacheid found"}), mimetype="application/json")
    
    proxyurl = settings.HTTPPROXYURL + "/Page?" + cacheid
    result = { 'proxyurl':proxyurl, 'cacheid':cacheid }
    
    try:
        fin = urllib2.urlopen(proxyurl)
        result["mimetype"] = fin.headers.type or "text/html"
        if fin.headers.maintype == 'text' or fin.headers.type == "application/json" or fin.headers.type[-4:] == "+xml":
            result['content'] = convtounicode(fin.read())
        else:
            result['content'] = base64.encodestring(fin.read())
            result['encoding'] = "base64"
    except urllib2.URLError, e: 
        result['type'] = 'exception'
        result['content'] = str(e)
    except BadStatusLine, sl:
        result['type'] = 'exception'
        result['content'] = str(sl)
    except Exception, exc:
        result['type'] = 'exception'
        result['content'] = str(exc)
    
    return HttpResponse(json.dumps(result), mimetype="application/json")


def export_csv(request, short_name):
    tablename = request.GET.get('tablename', "swdata")
    query = "select * from `%s`" % tablename
    qsdata = { "name":short_name.encode('utf-8'), "query":query.encode('utf-8'), "format":"csv" }
    return HttpResponseRedirect("%s?%s" % (reverse("api:method_sqlite"), urllib.urlencode(qsdata)))


    # could be replaced with the dataproxy chunking technology now available in there,
    # but as it's done, leave it here
def stream_sqlite(dataproxy, filesize, memblock):
    for offset in range(0, filesize, memblock):
        sqlitedata = dataproxy.request({"maincommand":"sqlitecommand", "command":"downloadsqlitefile", "seek":offset, "length":memblock})
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
    memblock=100000
    
    dataproxy = DataStore(scraper.short_name)
    initsqlitedata = dataproxy.request({"maincommand":"sqlitecommand", "command":"downloadsqlitefile", "seek":0, "length":0})
    if "filesize" not in initsqlitedata:
        return HttpResponse(str(initsqlitedata), mimetype="text/plain")
    
    response = HttpResponse(stream_sqlite(dataproxy, initsqlitedata["filesize"], memblock), mimetype='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s.sqlite' % (short_name)
    response["Content-Length"] = initsqlitedata["filesize"]
    return response

def attachauth(request):
    # aquery = {"command":"can_attach", "scrapername":self.short_name, "attachtoname":name, "username":"unknown"}
    scrapername = request.GET.get("scrapername")
    attachtoname = request.GET.get("attachtoname")

    try:
        attachtoscraper = models.Code.objects.exclude(privacy_status="deleted").get(short_name=attachtoname)
    except models.Code.DoesNotExist:
        return HttpResponse("DoesNotExist")

    if attachtoscraper.privacy_status != "private":
        return HttpResponse("Yes")
        
    if not scrapername:
        return HttpResponse("Draft scraper can't connect to private scraper: %s" % str([attachtoname]))

    try:
        scraper = models.Code.objects.exclude(privacy_status="deleted").get(short_name=scrapername)
    except models.Code.DoesNotExist:
        return HttpResponse("Scraper does not exist: %s" % str([scrapername]))

    if scraper.privacy_status == 'public':
        return HttpResponse("No: because scraper connecting from is public")
        

    # we're going to use the set of editors of a private/protected scraper be the gateway for access to the 
    # private attach to scraper (success if there is an overlap in the sets)
    scraperuserroles = models.UserCodeRole.objects.filter(code=scraper)
    attachtouserroles = models.UserCodeRole.objects.filter(code=attachtoscraper)
    usersofattach = [ usercoderole.user  for usercoderole in attachtouserroles  if usercoderole.role in ['owner', 'editor'] ]
    usersofscraper = [ usercoderole.user  for usercoderole in scraperuserroles  if usercoderole.role in ['owner', 'editor'] ]
    commonusers = set(usersofattach).intersection(set(usersofscraper))
    if not commonusers:
        return HttpResponse("No: because no common owners or editors between the two scrapers")
        
    return HttpResponse("Yes")
    
