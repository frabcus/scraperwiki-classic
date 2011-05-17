import urllib
import urllib2

from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from settings import MAX_API_ITEMS, API_DOMAIN
from django.views.decorators.http import condition
from tagging.models import Tag

import csv
import datetime
import re

from django.utils.encoding import smart_str
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.utils import simplejson


from codewiki.models import Scraper, Code, ScraperRunEvent, scraper_search_query
from codewiki.managers.datastore import DataStore
from cStringIO import StringIO

try:     import json
except:  import simplejson as json


def getscraperorresponse(request, action):
    message = None
    try:
        scraper = Code.objects.exclude(privacy_status="deleted").get(short_name=request.GET.get('name'))
    except Code.DoesNotExist:
        message =  "Sorry, this datastore does not exist"
    
    if not message and scraper.actionauthorized(request.user, "apidataread"):
        return scraper
        
    result = json.dumps({'error':message})
    callback = request.GET.get("callback")
    if callback:
        result = "%s(%s)" % (callback, result)
    return HttpResponse(result)



# see http://stackoverflow.com/questions/1189111/unicode-to-utf8-for-csv-files-python-via-xlrd
def stringnot(v):
    if v == None:
        return ""
    if type(v) in [unicode, str]:
        return v.encode("utf-8")
    return v


def stream_csv(dataproxy):
    n = 0
    while True:
        line = dataproxy.receiveonelinenj()
        try:
            ret = simplejson.loads(line)
        except ValueError, e:
            yield str(e)
            break
        if "error" in ret:
            yield str(ret)
            break
        fout = StringIO()
        writer = csv.writer(fout, dialect='excel')
        if n == 0:
            writer.writerow([ k.encode('utf-8') for k in ret["keys"] ])
        for row in ret["data"]:
            writer.writerow([ stringnot(v)  for v in row ])
        
        yield fout.getvalue()
        n += 1
        if not ret.get("moredata"):
            break  


def data_handler(request):
    tablename = request.GET.get('tablename', "swdata")
    squery = ["select * from `%s`" % tablename]
    if "limit" in request.GET:
        squery.append('limit %s' % request.GET.get('limit'))
    if "offset" in request.GET:
        squery.append('offset %s' % request.GET.get('offset'))
    qsdata = { "name": request.GET.get("name", "").encode('utf-8'), "query": " ".join(squery).encode('utf-8') }
    if "format" in request.GET:
        qsdata["format"] = request.GET.get("format").encode('utf-8')
    if "callback" in request.GET:
        qsdata["callback"] = request.GET.get("callback").encode('utf-8')
    return HttpResponseRedirect("%s?%s" % (reverse("api:method_sqlite"), urllib.urlencode(qsdata)))

    

# ***Streamchunking could all be working, but for not being able to set the Content-Length
# inexact values give errors in apache, so it would be handy if it could have a setting where 
# it organized some chunking instead

# see http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
# setting the Content-Length to -1 to prevent middleware from consuming the generator to measure it
# causes an error in the apache server.  same for a too long content length
# Should consider giving transfer-coding: chunked, 
# http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.6

# streaming is only happening from the dataproxy into here.  Streaming from here out through django is 
# nearly impossible as we don't know the length of the output file if we incrementally build the csv output
# the generator code has therefore been undone
# all for want of setting response["Content-Length"] to the correct value
@condition(etag_func=None)
def sqlite_handler(request):
    scraper = getscraperorresponse(request, "apidataread")
    if isinstance(scraper, HttpResponse):  return scraper
    dataproxy = DataStore(request.GET.get('name'))
    lattachlist = request.GET.get('attach', '').split(";")
    attachlist = [ ]
    for aattach in lattachlist:
        if aattach:
            aa = aattach.split(",")
            attachi = {"name":aa[0], "asname":(len(aa) == 2 and aa[1] or None)}
            attachlist.append(attachi)
            dataproxy.request({"maincommand":"sqlitecommand", "command":"attach", "name":attachi["name"], "asname":attachi["asname"]})
    
    sqlquery = request.GET.get('query', "")
    format = request.GET.get("format", "json")
    if format == "json":
        format = "jsondict"
    
    req = {"maincommand":"sqliteexecute", "sqlquery":sqlquery, "data":None, "attachlist":attachlist}
    if format == "csv":
        req["streamchunking"] = 1000
    
    # this is inlined from the dataproxy.request() function to allow for receiveoneline to perform multiple readlines in this case
        # (this is the stream-chunking thing.  the right interface is not yet apparent)
    dataproxy.m_socket.sendall(simplejson.dumps(req) + '\n')
    
    if format not in ["csv", "jsondict", "jsonlist"]:
        return HttpResponse("Error: the format '%s' is not supported" % format)
    
    if format == "csv":
        st = stream_csv(dataproxy)
        response = HttpResponse(mimetype='text/csv')  # used to take st
        #response = HttpResponse(st, mimetype='text/csv')  # when streamchunking was tried
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % (scraper.short_name)
        for s in st:
            response.write(s)
        # unless you put in a content length, the middleware will measure the length of your data
        # (unhelpfully consuming everything in your generator) before then returning a zero length result 
        #response["Content-Length"] = 1000000000
        return response
    
    # json is not chunked.  The output is of finite fixed bite sizes because it is generally used by browsers which aren't going to survive a huge download
    result = dataproxy.receiveonelinenj()
    if format == "jsondict":
        try:
            res = simplejson.loads(result)
        except ValueError, e:
            return HttpResponse("Error:%s" % (e.message,))
        if "error" not in res:
            dictlist = [ dict(zip(res["keys"], values))  for values in res["data"] ]
            result = simplejson.dumps(dictlist, cls=DateTimeAwareJSONEncoder, indent=4)
    callback = request.GET.get("callback")
    if callback:
        result = "%s(%s)" % (callback, result)
    response = HttpResponse(result, mimetype='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=%s.json' % (scraper.short_name)
    return response


def scraper_search_handler(request):
    query = request.GET.get('query') 
    if not query:
        query = request.GET.get('searchquery') 
    try:   
        maxrows = int(request.GET.get('maxrows', ""))
    except ValueError: 
        maxrows = 5
    result = [ ]  # list of dicts
    scrapers = scraper_search_query(user=None, query=query)
    for scraper in scrapers[:maxrows]:
        res = {'short_name':scraper.short_name }
        res['title'] = scraper.title
        owners = scraper.userrolemap()["owner"]
        if owners:
            owner = owners[0]
            ownername = owner.get_profile().name
            if not ownername:
                ownername = owner.username
            if ownername:
                res['title'] = "%s / %s" % (ownername, scraper.title)
        res['description'] = scraper.description
        res['created'] = scraper.created_at.isoformat()
        res['privacy_status'] = scraper.privacy_status
        result.append(res)
    
    if request.GET.get("format") == "csv":
        fout = StringIO()
        writer = csv.writer(fout, dialect='excel')
        headers = [ 'short_name', 'title', 'description', 'created', 'privacy_status' ]
        writer.writerow(headers)
        for r in result:
            writer.writerow([r[header]  for header in headers])
        response = HttpResponse(fout.getvalue(), mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=search.csv'
        return response
    
    res = json.dumps(result, indent=4)
    callback = request.GET.get("callback")
    if callback:
        res = "%s(%s)" % (callback, res)
    response = HttpResponse(res, mimetype='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=search.json'
    return response




def userinfo_handler(request):
    username = request.GET.get('username', "") 
    users = User.objects.filter(username=username)
    result = [ ]
    for user in users:  # list of users is normally 1
        info = { "username":user.username, "profilename":user.get_profile().name }
        info["datejoined"] = user.date_joined.isoformat()
        info['coderoles'] = { }
        for ucrole in user.usercoderole_set.exclude(code__privacy_status="deleted").exclude(code__privacy_status="private"):
            if ucrole.role not in info['coderoles']:
                info['coderoles'][ucrole.role] = [ ]
            info['coderoles'][ucrole.role].append(ucrole.code.short_name)

        info['fromuserroles'] = { }
        for fromuserrole in user.from_user.all():
            if fromuserrole.role not in info['fromuserroles']:
                info['fromuserroles'][fromuserrole.role] = [ ]
            info['fromuserroles'][fromuserrole.role].append(fromuserrole.from_user.username)
        
        info['touserroles'] = { }
        for touserrole in user.to_user.all():
            if touserrole.role not in info['touserroles']:
                info['touserroles'][touserrole.role] = [ ]
            info['touserroles'][touserrole.role].append(touserrole.to_user.username)
        
        result.append(info)
    
    res = json.dumps(result, indent=4)
    callback = request.GET.get("callback")
    if callback:
        res = "%s(%s)" % (callback, res)
    response = HttpResponse(res, mimetype='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=userinfo.json'
    return response




def runevent_handler(request):
    scraper = getscraperorresponse(request, "apiscraperruninfo")
    if isinstance(scraper, HttpResponse):  return scraper
    runid = request.GET.get('runid', '-1')
    runevent = None
    if runid[0] == '-':   # allow for negative indexes to get to recent runs
        try:
            i = -int(runid)
            runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')
            if i < len(runevents):
                runevent = runevents[i]
        except ValueError:
            pass
    if not runevent:
        try:
            runevent = scraper.scraper.scraperrunevent_set.get(run_id=runid)
        except ScraperRunEvent.DoesNotExist:
            return HttpResponse("Error: run object not found")

    info = { "runid":runevent.run_id, "run_started":runevent.run_started.isoformat(), 
                "records_produced":runevent.records_produced, "pages_scraped":runevent.pages_scraped, 
            }
    if runevent.run_ended:
        info['run_ended'] = runevent.run_ended.isoformat()
    if runevent.exception_message:
        info['exception_message'] = runevent.exception_message
    
    info['output'] = runevent.output
    if runevent.first_url_scraped:
        info['first_url_scraped'] = runevent.first_url_scraped
    
    domainsscraped = [ ]
    for domainscrape in runevent.domainscrape_set.all():
        domainsscraped.append({'domain':domainscrape.domain, 'bytes':domainscrape.bytes_scraped, 'pages':domainscrape.pages_scraped})
    if domainsscraped:
        info['domainsscraped'] = domainsscraped
        
    result = [info]      # a list with one element
    res = json.dumps(result, indent=4)
    callback = request.GET.get("callback")
    if callback:
        res = "%s(%s)" % (callback, res)
    response = HttpResponse(res, mimetype='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=runevent.json'
    return response



def convert_history(commitentry):
    result = { 'version':commitentry['rev'], 'date':commitentry['date'].isoformat() }
    if 'user' in commitentry:
        result["user"] = commitentry['user'].username
    lsession = commitentry['description'].split('|||')
    if len(lsession) == 2:
        result['session'] = lsession[0]
    return result

def convert_run_event(runevent):
    result = { "runid":runevent.run_id, "run_started":runevent.run_started.isoformat(), 
                "records_produced":runevent.records_produced, "pages_scraped":runevent.pages_scraped, 
                "still_running":(runevent.pid != -1),
                }
    if runevent.run_ended:
        result['last_update'] = runevent.run_ended.isoformat()
    if runevent.exception_message:
        result['exception_message'] = runevent.exception_message
    return result

def convert_date(date_str):
    if not date_str:
        return None
    try:
        #return datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return datetime.datetime(*map(int, re.findall("\d+", date_str)))  # should handle 2011-01-05 21:30:37
    except ValueError:
        return None


def scraperinfo_handler(request):
    scraper = getscraperorresponse(request, "apiscraperinfo")
    if isinstance(scraper, HttpResponse):  return scraper
    history_start_date = convert_date(request.GET.get('history_start_date', None))
    quietfields        = request.GET.get('quietfields', "").split("|")
        
    info = { }
    info['short_name']  = scraper.short_name
    info['language']    = scraper.language
    info['created']     = scraper.created_at.isoformat()
    
    info['title']       = scraper.title
    info['description'] = scraper.description
    info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
    info['wiki_type']   = scraper.wiki_type
    info['privacy_status'] = scraper.privacy_status
    if scraper.wiki_type == 'scraper':
        info['license']     = scraper.scraper.license
        info['records']     = scraper.scraper.record_count  # old style datastore
        
        if 'datasummary' not in quietfields:
            dataproxy = DataStore(scraper.short_name)
            sqlitedata = dataproxy.request({"maincommand":"sqlitecommand", "command":"datasummary", "val1":0, "val2":None})
            if sqlitedata and type(sqlitedata) not in [str, unicode]:
                info['datasummary'] = sqlitedata
    
    if 'userroles' not in quietfields:
        info['userroles']   = { }
        for ucrole in scraper.usercoderole_set.all():
            if ucrole.role not in info['userroles']:
                info['userroles'][ucrole.role] = [ ]
            info['userroles'][ucrole.role].append(ucrole.user.username)
            
    try: 
        rev = int(request.GET.get('version', ''))
    except ValueError: 
        rev = None
        
    status = scraper.get_vcs_status(rev)
    if 'code' not in quietfields:
        info['code']        = status["code"]
    
    for committag in ["currcommit", "prevcommit", "nextcommit"]:
        if committag in status:
            info[committag] = convert_history(status[committag])
    
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        if 'filemodifieddate' in status:
            info["modifiedcommitdifference"] = str(status["filemodifieddate"] - status["prevcommit"]["date"])
            info['filemodifieddate'] = status['filemodifieddate'].isoformat()

    if history_start_date:
        history = [ ]
        commitentries = scraper.get_commit_log()
        for commitentry in commitentries:
            if commitentry['date'] < history_start_date:
                continue
            history.append(convert_history(commitentry))
        history.reverse()
        info['history'] = history
    
    if scraper.wiki_type == 'scraper' and 'runevents' not in quietfields:
        if history_start_date:
            runevents = scraper.scraper.scraperrunevent_set.filter(run_ended__gte=history_start_date).order_by('-run_started')
        else:
            runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')[:2]
            
        info['runevents'] = [ ]
        for runevent in runevents:
            info['runevents'].append(convert_run_event(runevent))

    result = [info]      # a list with one element
    res = json.dumps(result, indent=4)
    callback = request.GET.get("callback")
    if callback:
        res = "%s(%s)" % (callback, res)
    response = HttpResponse(res, mimetype='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=scraperinfo.json'
    return response


