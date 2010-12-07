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

try:                import json
except ImportError: import simplejson as json



def MakeRunner(request, short_name, revision = None):
    scraper = get_object_or_404(models.Code.objects, short_name=short_name)
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
    code = scraper.saved_code(revision)
    runner.stdin.write(code.encode('utf8'))
    
    # append in the single line at the bottom that gets the rpc executed with the right function and arguments
    #if func:
    #    runner.stdin.write("\n\n%s(**%s)\n" % (func, repr(rargs)))

    runner.stdin.close()
    return runner


def rpcexecute(request, short_name, revision = None):
    runner = MakeRunner(request, short_name, revision)

    # we build the response on the fly in case we get a contentheader value before anything happens
    response = None # HttpResponse()
    
    for line in runner.stdout:
        print line
        try:
            message = json.loads(line)
        except:
            pass
            
        if message['message_type'] == 'exception':
            if not response:
                response = HttpResponse()
            
            response.write("<h3>%s</h3>\n" % str(message["jtraceback"].get("exceptiondescription")).replace("<", "&lt;"))
            for stackentry in message["jtraceback"]["stackdump"]:
                response.write("<h3>%s</h3>\n" % re.replace("<", "&lt;", str(stackentry).replace("<", "&lt;")))

        elif message['message_type'] == "contentheader":
            if not response:
                response = HttpResponse(mimetype=re.sub('Content-Type:\s*', '', message['content']))
            else:
                response.write("<h3>Error content type added after start of stream: %s</h3>" % message['content'])
        
        elif message['message_type'] == "console":
            if not response:
                response = HttpResponse()
            
            response.write(message["content"])

    return response
                
                
                
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

