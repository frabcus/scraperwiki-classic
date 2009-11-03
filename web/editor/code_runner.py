import re
import sys
import os
import datetime
import string
import simplejson as json

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
        if line.startswith('<scraperwiki:message type="data">'):
            message_type = "data"
        elif line.startswith('<scraperwiki:message type="sources">'):
            message_type = "sources"
        else:
            message_type = "console"
        ret.append(json.dumps({'message_type' : message_type, 'content' : line}) + "@@||@@")
    return '\n'.join(ret)

def run_code(request):
  code = request.POST.get('code', False)
  if code:
    run_mode = settings.CODE_RUNNING_MODE
  
    if run_mode == 'popen':
    
      res =  format_json(run_popen(code))
      return HttpResponse(res)
      
    if run_mode == 'firestarter_django':
      return run_firestarter_django(code)



# Information about paths:

# settings.SCRAPERWIKI_LIB_DIR 
#     contains scraperwiki/ so we can write "import scraperwiki.usefulmodule" at the top of a scraper
# settings.SMODULES_DIR 
#     points to scrapers/ so we can write "import missingcats" (another scraper), or run the process by giving the UML just the code "import missingcats; missingcats.Parse()" 
#     rather than the entire contents of missingcats.__init__py file to execute
#     (this one needs a new name, eg SCRAPERS_DIR)  But it's awkward to change because its set in localsettings.py because it points to a different mercurial repository
# settings.SCRAPERWIKI_DIR 
#     is the top level web/ directory which allows us to write "import scrapers.missingcats", 
#     which looks better, but unfortunately allows access to other top level modules it shouldn't have access to.  
#     We're going to need to put the scrapers/ directory in its own directory (eg scraperwikilib/) 
#     that controls the range of the import function.  

def run_popen(code):
  import tempfile
  import subprocess
  
  fout = tempfile.NamedTemporaryFile(suffix=".py")
  fout.write(code)
  fout.flush()
  cmd = "python %s" % (fout.name)
  
  # first one is necessary if to run codelets "import scrapers.missingcats; missingcats.Parse()"
  #env = { "DJANGO_SETTINGS_MODULE":'settings', "PYTHONPATH":"%s:%s:%s" % (settings.SCRAPER_LIBS_DIR, settings.SMODULES_DIR, settings.SCRAPERWIKI_DIR) }
  env = { "DJANGO_SETTINGS_MODULE":'settings', "PYTHONPATH":"%s" % (settings.SCRAPER_LIBS_DIR) }  # PYTHONPATH delimited by : character
  print "eeee", env
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
  
  
  
  
