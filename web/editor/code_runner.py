import re
import sys
import os
import datetime
import string
try:
    import simplejson as json
except:
    import json
    
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from scraper.models import Scraper as ScraperModel, UserScraperRole
from scraper import template
from scraper import vc
import forms
import settings

def format_json(lines):
    ret = []
    for line in lines.splitlines():
        if line.startswith('<message type="data">'):
            message_type = "data"
        elif line.startswith('<message type="sources">'):
            message_type = "sources"
        else:
            message_type = "console"
        ret.append(json.dumps({'type' : message_type, 'content' : line}))
    return '\n'.join(ret)



def run_code(request):
  code = request.POST.get('code', False)
  guid = request.POST.get('guid', False)
  if code:
    run_mode = settings.CODE_RUNNING_MODE
  
    if run_mode == 'popen':
    
      res =  format_json(run_popen(code, guid=guid))
      return HttpResponse(res)
      
    if run_mode == 'firestarter_django':
      return format_json(run_firestarter_django(code))


def run_popen(code, guid=False):
  import tempfile
  import subprocess
  
  fout = tempfile.NamedTemporaryFile(suffix=".py")
  fout.write(code)
  fout.flush()
  cmd = "python %s" % (fout.name)
  path = sys.path
 
  
  path.append('/var/www/scraperwiki/clean2/')
  env = { 
    "DJANGO_SETTINGS_MODULE":'settings', 
    "PYTHONPATH": "%s" % (':'.join(path)),
    "SCRAPER_GUID":"%s" % (guid),
    }
  p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, env=env)
  res = p.stdout.readlines()
  fout.close()   # deletes the temporary file
  return ''.join(res)


def run_firestarter_django(code):
  import FireStarter
  fb   = FireStarter.FireStarter()
  fb.addPaths ('/a', '/b')
  code = string.replace (code, '\r', '')

  res  = fb.execute(code, True)
  line = res.readline()
  lines = []
  while line is not None and line != '':
    lines.append(line)
    line  = res.readline()
  return '\n'.join(lines)
  
  
  
  
  