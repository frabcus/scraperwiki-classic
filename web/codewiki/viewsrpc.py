from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from django.conf import settings

from codewiki import models, runsockettotwister
import frontend
import urllib
import subprocess
import re
import base64
import cgi

try:                import json
except ImportError: import simplejson as json


def MakeRunner(request, scraper, code):
    runner_path = "%s/runner.py" % settings.FIREBOX_PATH
    failed = False

    urlquerystring = request.META["QUERY_STRING"]
    
    # append post values to the query string (so we can consume them experimentally)
    # we could also be passing in the sets of scraper environment variables in this way too
    # though maybe we need a generalized version of the --urlquery= that sets an environment variables explicitly
    # the bottleneck appears to be the runner.py command line instantiation
    # (POST is a django.http.QueryDict which destroys information about the order of the incoming parameters) 
    if list(request.POST):
        qsl = cgi.parse_qsl(urlquerystring)
        qsl.extend(request.POST.items())
        urlquerystring = urllib.urlencode(qsl)
        print "sending in new querystring:", urlquerystring
    
    
    args = [ runner_path.encode('utf8') ]
    args.append('--guid=%s' % scraper.guid.encode('utf8'))
    args.append('--language=%s' % scraper.language.lower().encode('utf8'))
    args.append('--name=%s' % scraper.short_name.encode('utf8'))
    args.append('--cpulimit=80')
    args.append('--urlquery=%s' % urlquerystring.encode('utf8'))
    
    runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    runner.stdin.write(code.encode('utf8'))
    
    runner.stdin.close()
    return runner



def scraperwikitag(scraper, html, panepresent):
    mswpane = re.search('(?i)<div[^>]*?id="scraperwikipane"[^>/]*(?:/\s*>|>.*?</div>)', html)
    if mswpane:
        startend = (mswpane.start(0), mswpane.end(0))
        mclass = re.search('class="([^"]*)"', mswpane.group(0))
        if mclass:
            paneversion = mclass.group(1)
        else:
            paneversion = "version-2"
        if panepresent != None:
            panepresent["scraperwikipane"].append(mswpane)
    
    elif panepresent == None:  # case where no div#scraperwikipane is found and it's all there (we're not streaming the html out using php)
        # have to insert the pane -- favour doing it after the body tag if it exists
        mbody = re.search("(?i)<body.*?>", html)
        if mbody:
            startend = (mbody.end(0), mbody.end(0))
        else:
            startend = (0, 0) # (0,0)
        paneversion = "version-2"
    
    else:
        if len(panepresent["firstfivelines"]) < 5 and re.search("\S", html):
            panepresent["firstfivelines"].append(html)
        return html
    
    
    urlbase = settings.MAIN_URL
    urlscraperoverview = urlbase + reverse('code_overview', args=[scraper.wiki_type, scraper.short_name])
    urlscraperedit = urlbase + reverse('editor_edit', args=[scraper.wiki_type, scraper.short_name])
    urlpoweredlogo = settings.MEDIA_URL + "images/powered.png";
    
    swdivstyle = "border:thin #aaf solid; display:block; position:fixed; top:0px; right:0px; background:#eef; margin: 0em; padding: 6pt; font-size: 10pt; z-index: 8675309; "
    swlinkstyle = "width:167px; height:17px; margin:0; padding: 0; border-style: none; "

    if paneversion == "version-1":
        swpane = [ '<div id="scraperwikipane" style="%s;">' % swdivstyle ]
        swpane.append('<a href="%s" id="scraperwikipane" style="%s"><img style="border-style: none" src="%s" alt="Powered by ScraperWiki"></a>' % (urlbase, swlinkstyle, urlpoweredlogo))
        swpane.append('<br><a href="%s" title="Go to overview page">%s</a>' % (urlscraperoverview, scraper.title))
        swpane.append(' (<a href="%s" title="Edit source code for this view">edit</a>)' % (urlscraperedit))
        swpane.append('</div>')
    
    else:
        swpane = [ '<div id="scraperwikipane" style="%s;">' % swdivstyle ]
        swpane.append('<a href="%s" id="scraperwikipane" style="%s"><img style="border-style: none" src="%s" alt="Powered by ScraperWiki"></a>' % (urlscraperoverview, swlinkstyle, urlpoweredlogo))
        swpane.append('</div>')

    return "%s%s%s" % (html[:startend[0]], "".join(swpane), html[startend[1]:])


def rpcexecute(request, short_name, revision=None):
    try:
        scraper = models.Code.objects.get(short_name=short_name)
    except models.Code.DoesNotExist:
        return HttpResponseNotFound(render_to_string('404.html', {'heading':'Not found', 'body':"Sorry, this view does not exist"}, context_instance=RequestContext(request)))
    if not scraper.actionauthorized(request.user, "rpcexecute"):
        return HttpResponseNotFound(render_to_string('404.html', scraper.authorizationfailedmessage(request.user, "rpcexecute"), context_instance=RequestContext(request)))
    
    if revision:
        try: 
            revision = int(revision)
        except ValueError: 
            revision = None
    code = scraper.saved_code(revision)
    
    # quick case where we have PHP with no PHP code in it (it's all pure HTML)
    if scraper.language == 'php' and not re.search('<\?', code):
        return HttpResponse(scraperwikitag(scraper, code, None))
    if scraper.language == 'html':
        return HttpResponse(scraperwikitag(scraper, code, None))
    if scraper.language == 'javascript':
        HttpResponse(code, mimetype='application/javascript')

    
    # run it the socket method for staff members who can handle being broken
    if request.user.is_staff:
        runnerstream = runsockettotwister.RunnerSocket()
        runnerstream.runview(request.user, scraper, revision, request.META["QUERY_STRING"])
    else:
        runner = MakeRunner(request, scraper, code)
        runnerstream = runner.stdout

    # we build the response on the fly in case we get a contentheader value before anything happens
    response = None 
    panepresent = {"scraperwikipane":[], "firstfivelines":[]}
    contenttypesettings = { }
    for line in runnerstream:
        try:
            message = json.loads(line)
        except:
            pass
            
        if message['message_type'] == "console":
            if not response:
                response = HttpResponse()

            if message.get('encoding') == 'base64':
                response.write(base64.decodestring(message["content"]))
            else:
                response.write(scraperwikitag(scraper, message["content"], panepresent))
        
        elif message['message_type'] == 'exception':
            if not response:
                response = HttpResponse()
            
            response.write("<h3>%s</h3>\n" % str(message.get("exceptiondescription")).replace("<", "&lt;"))
            for stackentry in message["stackdump"]:
                response.write("<h3>%s</h3>\n" % str(stackentry).replace("<", "&lt;"))

        
        # parameter values have been borrowed from http://php.net/manual/en/function.header.php
        elif message['message_type'] == "httpresponseheader":
            contenttypesettings[message['headerkey']] = message['headervalue']
            if message['headerkey'] == 'Content-Type':
                if not response:
                    response = HttpResponse(mimetype=message['headervalue'])
                else:
                    response.write("<h3>Error: httpresponseheader('%s', '%s') called after start of stream</h3>" % (message['headerkey'], message['headervalue']))
                    
            elif message['headerkey'] == 'Content-Disposition':
                if not response:
                    response = HttpResponse()
                response['Content-Disposition'] = message['headervalue']
            
            elif message['headerkey'] == 'Location':
                if not response:
                    response = HttpResponseRedirect(message['headervalue'])
                else:
                    response.write("<h3>Error: httpresponseheader('%s', '%s') called after start of stream</h3>" % (message['headerkey'], message['headervalue']))
            
            else:
                if not response:
                    response = HttpResponse()
                response.write("<h3>Error: httpresponseheader(headerkey='%s', '%s'); headerkey can only have values 'Content-Type' or 'Content-Disposition'</h3>" % (message['headerkey'], message['headervalue']))
            
                    
    if not response:
        response = HttpResponse('no output for some unknown reason')
        
    # now decide about inserting the powered by scraperwiki panel (avoid doing it on json)
    # print [response['Content-Type']]  default is DEFAULT_CONTENT_TYPE, comes out as 'text/html; charset=utf-8'
    if not panepresent["scraperwikipane"]:
        firstcode = "".join(panepresent["firstfivelines"]).strip()
        if not contenttypesettings:   # suppress if content-type was set
            if not re.match("[\w_\s=]*[\(\[\{]", firstcode):   # looks like it is not json code
                if re.search("(?i)<\s*(?:b|i|a|h\d|script|ul|table).*?>", firstcode):   # looks like it is html
                    response.write(scraperwikitag(scraper, '<div id="scraperwikipane" class="version-2"/>', panepresent))
    
    return response
                
                

# liable to hang if UMLs not operative
def testactiveumls(n):
    result = [ ]
    code = "from subprocess import Popen, PIPE\nprint Popen(['hostname'], stdout=PIPE).communicate()[0]"
    
    runner_path = "%s/runner.py" % settings.FIREBOX_PATH
    args = [runner_path, '--language=python', '--cpulimit=80']
    
    for i in range(n):
        runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        runner.stdin.write(code)
        runner.stdin.close()
        
        lns = [ ]
        for line in runner.stdout:
            message = json.loads(line)
            if message['message_type'] == "console":
                if message.get('message_sub_type') != 'consolestatus':
                    lns.append(message['content'].strip())
            elif message['message_type'] == "executionstatus":
                pass
            else:
                lns.append(line)
        result.append('\n'.join(lns))
    return result

def overdue_scrapers(request):
    if request.GET.get("django_key") == runsockettotwister.config.get('twister', 'djangokey') or request.user.is_staff:
        scrapers = models.scrapers_overdue()
        return HttpResponse(json.dumps([(float(scraper.overdue_proportion), scraper.short_name)  for scraper in scrapers]))
    return HttpResponse("Not authorized")
