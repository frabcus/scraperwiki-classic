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

import csv
from django.utils.encoding import smart_str
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.utils import simplejson


from codewiki.models import Scraper, Code
from codewiki.managers.datastore import DataStore

from django.contrib.auth.decorators import login_required

from models import api_key
from forms import applyForm
from cStringIO import StringIO

import base64

def getscraperorresponse(request):
    try:
        scraper = Code.objects.exclude(privacy_status="deleted").get(short_name=request.GET.get('name'))
    except Code.DoesNotExist:
        message =  "Sorry, this datastore does not exist"
        return HttpResponse(str({'heading':'Not found', 'body':message}))
    
    if not scraper.actionauthorized(request.user, "apidataread"):
        return HttpResponse(str(scraper.authorizationfailedmessage(request.user, "apidataread")))
    return scraper


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
        if "moredata" not in ret:
            break  


def data_handler(request):
    tablename = request.GET.get('tablename', "swdata")
    squery = ["select * from `%s`" % tablename]
    if "limit" in request.GET:
        squery.append('limit %s' % request.GET.get('limit'))
    if "offset" in request.GET:
        squery.append('offset %s' % request.GET.get('offset'))
    qsdata = { "name": request.GET.get("name").encode('utf-8'), "query": " ".join(squery).encode('utf-8') }
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
    scraper = getscraperorresponse(request)
    if isinstance(scraper, HttpResponse):  return scraper
    dataproxy = DataStore("sqlviewquery", "")  # zero length short name means it will open up a :memory: database

    attachlist = request.GET.get('attach', '').split(";")
    attachlist.insert(0, request.GET.get('name'))   # just the first entry on the list
        
    for aattach in attachlist:
        if aattach:
            aa = aattach.split(",")
            sqlitedata = dataproxy.request(("sqlitecommand", "attach", aa[0], (len(aa) == 2 and aa[1] or None)))
    
    sqlquery = request.GET.get('query', "")
    format = request.GET.get("format", "json")
    if format == "json":
        format = "jsondict"
    
    reqt = None
    if format == "csv":
        reqt = ("streamchunking", 1000)
    req = ("sqlitecommand", "execute", sqlquery, reqt)
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

