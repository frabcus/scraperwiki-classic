import os
import re
import sys
import stat
import datetime
import difflib
import time
import subprocess

import settings
import codewiki.models as models



# The HttpResponse::flush() commands is just a stub that does nothing.  I can find no equivalent to php::flush()
# See http://stackoverflow.com/questions/219329/django-fastcgi-how-to-manage-a-long-running-process for same issue
# Refers to http://code.google.com/p/django-queue-service/ which would precisely solve the whole problem

# this produces an iterator that should in theory dribble the output lines out.
# except it doesn't.  and even if the dribbling out is simulated, the Django doesn't dribble the output.
def RunFileA(exename, arg):
    
    #yield "AAjax streameds output %s %s\n" % (exename, arg)
    #GetLastLogline(exename)
    
    #f1, f2 = os.popen4("python " + fname + " " + arg)
    cmd = "python %s %s" % (exename, arg)
    env = { "DJANGO_SETTINGS_MODULE":'settings', "PYTHONPATH":"%s:%s" % (settings.SMODULES_DIR, settings.SCRAPERWIKI_DIR) }
    print "RUNNING:", cmd
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, env=env)
    
    ln = 0
    while True:
        #txt = p.stdout.next()
        txt = p.stdout.readline()
        if not txt:
            break
        #print "------ yield", [txt]
        #time.sleep(1.4)
        yield txt
        
        ln += 1
        if ln > 6000:
            yield "==More than 6000 lines==\n"
            break
    yield "==End==\n"

    
def RunSButtCode(scrapermodule, sbutt, vals):
    exename = os.path.join(settings.SCRAPERWIKI_DIR, "scraperutils.py")
    for ln in RunFileA(exename, "%s %s %s" % (scrapermodule.modulename, sbutt, vals)):
        yield ln
        

