from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from django.db import IntegrityError
from django.contrib.auth.models import User

from django.conf import settings

from codewiki import models
import vc
import frontend
import urllib

import subprocess
import re
import base64

try:                import json
except ImportError: import simplejson as json



def MakeRunner(request, scraper, code):
    runner_path = "%s/runner.py" % settings.FIREBOX_PATH
    failed = False

    urlquerystring = request.META["QUERY_STRING"]
    # derive the function and arguments from the urlargs
    # (soon to be deprecated)
    rargs = { }
    for key in request.GET.keys():
        rargs[str(key)] = request.GET.get(key)
    func = rargs.pop("function", None)
    for key in rargs.keys():
        try: 
            rargs[key] = json.loads(rargs[key])
        except:
            pass
    
    args = [runner_path]
    args.append('--guid=%s' % scraper.guid)
    args.append('--language=%s' % scraper.language.lower())
    args.append('--name=%s' % scraper.short_name)
    args.append('--cpulimit=80')
    args.append('--urlquery=%s' % urlquerystring)
    args = [i.encode('utf8') for i in args]
    
    runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    runner.stdin.write(code.encode('utf8'))
    
    # append in the single line at the bottom that gets the rpc executed with the right function and arguments
    #if func:
    #    runner.stdin.write("\n\n%s(**%s)\n" % (func, repr(rargs)))

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
    elif panepresent == None:
        startend = (0, 0) # (0,0)
        paneversion = "version-2"
    else:
        if len(panepresent["firstfivelines"]) < 5 and re.search("\S", html):
            panepresent["firstfivelines"].append(html)
        return html
    
    
    urlscraperoverview = reverse('code_overview', args=[scraper.wiki_type, scraper.short_name])
    urlscraperedit = reverse('editor_edit', args=[scraper.wiki_type, scraper.short_name])
    
    swdivstyle = "border:thin #aaf solid; display:block;width:225px; position:fixed; top:0px; right:0px; background:#eef; "
    swlinkstyle = "display:block;float:right; width:175px; height:20px; background:url(/media/images/powered.png) no-repeat;"
    lkbuttonstyle = "font-family:helvetica, arial, sans-serif; font-size:0.8em; position:relative; top:1px; background-color:#f1f1ff; border:solid 1px #bbb; padding:0.0em 0.2em!important; border-radius: 4px; -moz-border-radius: 4px; -webkit-border-radius: 4px;"
    
    if paneversion == "version-1":
        swpane = [ '<div id="scraperwikipane" style="%s">' % swdivstyle ]
        swpane.append('<b><a href="%s" title="Go to overview page">%s</a></b>' % (urlscraperoverview, scraper.title))
        swpane.append('<br/>')
        swpane.append('<a href="%s" title="Edit source code for this view" style="%s">Edit</a>' % (urlscraperedit, lkbuttonstyle))
        swpane.append('<a href="/" id="scraperwikipane" style="%s"><span style="display:none">Powered by ScraperWiki</span></a>' % swlinkstyle)
        swpane.append('</div>')

    else:
        swdivstyle = "border:thin #aaf solid; display:block;width:180px; position:fixed; top:0px; right:0px; background:#eef; "
        swpane = [ '<div id="scraperwikipane" style="%s">' % swdivstyle ]
        swpane.append('<a href="%s" id="scraperwikipane" style="%s"><span style="display:none">Powered by ScraperWiki</span></a>' % (urlscraperoverview, swlinkstyle))
        swpane.append('</div>')

    return "%s%s%s" % (html[:startend[0]], "".join(swpane), html[startend[1]:])


def rpcexecute(request, short_name, revision=None):
    scraper = get_object_or_404(models.Code.objects, short_name=short_name)
    code = scraper.saved_code(revision)
    
    # quick case where we have PHP with no PHP code in it (it's all pure HTML)
    if scraper.language == 'php' and not re.search('<\?', code):
        return HttpResponse(scraperwikitag(scraper, code, None))
    if scraper.language == 'html':
        return HttpResponse(scraperwikitag(scraper, code, None))
    if scraper.language == 'javascript':
        HttpResponse(code, mimetype='application/javascript')

    runner = MakeRunner(request, scraper, code)

        # we build the response on the fly in case we get a contentheader value before anything happens
    response = None 
    panepresent = {"scraperwikipane":[], "firstfivelines":[]}
    for line in runner.stdout:
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
        
    # now decide about inserting the powered by scraperwiki panel (avoid doint it on json)
    if not panepresent["scraperwikipane"]:
        firstcode = "".join(panepresent["firstfivelines"]).strip()
        if not re.match("[\w_\s=]*[\(\[\{]", firstcode):
            if re.search("(?i)<\s*(?:b|i|a|h\d|script|ul|table).*?>", firstcode):
                response.write(scraperwikitag(scraper, '<div id="scraperwikipane" class="version-1"/>', panepresent))
    
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

