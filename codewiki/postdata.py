import settings
import codewiki.models as models
from django.core import management
from django.db import connection
from django.contrib.auth.models import User
import re
import datetime
import os
import urllib
import runscrapers

# look in /usr/lib/python2.5/site-packages/django/core/management/ for extra functions

    
    #print "::::", len(reading.text), LoadReading(reading.id, reading.fileext)

def LoadReading(pageid, filename):
    reading = models.Reading(id=int(pageid))
    reading.filepath = os.path.join(settings.READINGS_DIR, filename)
    fin = open(reading.filepath, "r")
    ftext = fin.read()
    fin.close()
    mtailleng = re.search("tailleng=(\d+)$", ftext[-50:])
    
    if mtailleng:
        stail = int(mtailleng.group(1)) + len(mtailleng.group(0))
        reading.bytelength = len(ftext) - stail
        reading.text = ftext[:-stail]
        for k, lv in re.findall("<<<(.*?)=(.*?)>>>", ftext[-stail:]):
            v = urllib.unquote(lv)
            if k == "name":
                reading.name = v
            elif k == "scraper_tag":
                reading.scraper_tag = v
            elif k == "mimetype":
                reading.mimetype = v
            elif k == "url":
                reading.url = v
            elif k == "scrape_time":
                reading.scrape_time = v
            elif k == "id":
                assert reading.id == int(v)
    else:
        reading.bytelength = len(ftext)
        reading.text = ftext
        assert False   # just to trap
    
    if not reading.mimetype:
        reading.mimetype = "text/html"
    
    print pageid, reading
    reading.save()
    

def LoadReadings():
    for f in os.listdir(settings.READINGS_DIR):
        mpf = re.match("((\d+)\.+\w+)$", f)
        if mpf:
            LoadReading(int(mpf.group(2)), mpf.group(1))

def MakeModels():
    for scraperscript in models.ScraperScript.objects.filter(dirname='collectors'):
        exename = os.path.join(settings.MODULES_DIR, 'collectors', scraperscript.filename)
        print "mmmmmmmMM", exename
        difflistiter = runscrapers.RunFileA(exename, "makemodel") 
        print list(difflistiter)
    
def ResetScraperlist(dirname, subdirname):
    dname = os.path.join(settings.MODULES_DIR, dirname, subdirname)
    for f in os.listdir(dname):
        if re.match("\.|.*?~$|.*?\.pyc$", f):
            continue
        fname = os.path.join(dname, f)
        if os.path.isdir(fname):
            pass
            #ResetScraperlist(dirname, os.path.join(subdirname, f))
            #scrapermodule = models.ScraperModule(modulename=f, last_edit=datetime.datetime.fromtimestamp(os.stat(fname).st_mtime))
            #scrapermodule.save()
            
        elif f[-3:] == ".py":
            scraperscript = models.ScraperScript(dirname=dirname, filename=f, last_edit=datetime.datetime.fromtimestamp(os.stat(fname).st_mtime))
            scraperscript.modulename = f[:-3]
            scraperscript.save()

def ResetModulelist():
    for f in os.listdir(settings.SMODULES_DIR):
        if re.match("\.|.*?~$|.*?\.pyc$", f):
            continue
        fname = os.path.join(settings.SMODULES_DIR, f)
        if os.path.isdir(fname):
            scrapermodule = models.ScraperModule(modulename=f, last_edit=datetime.datetime.fromtimestamp(os.stat(fname).st_mtime))
            scrapermodule.save()

#
# This works for mySQL.  I have no idea how to do these functions in postgres
#
def ResetDatabase():
    cursor = connection.cursor()
    cursor.execute("drop database %s" % settings.DATABASE_NAME)
    cursor.execute("create database %s" % settings.DATABASE_NAME)
    cursor.execute("ALTER DATABASE %s CHARACTER SET=utf8" % settings.DATABASE_NAME)
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    management.call_command('syncdb', interactive=False)
    user = User.objects.create_user('m', 'm@m.com', 'm')
    user.is_staff = True
    user.is_superuser = True
    user.save()

    ResetScraperlist("readers", "")
    ResetScraperlist("detectors", "")
    ResetScraperlist("collectors", "")
    ResetScraperlist("observers", "")
    ResetModulelist()
    
    LoadReadings()
    MakeModels()



