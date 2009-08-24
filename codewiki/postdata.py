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
        if os.path.isdir(os.path.join(dname, f)):
            ResetScraperlist(dirname, os.path.join(subdirname, f))
        elif f[-3:] == ".py":
            scraperscript = models.ScraperScript(dirname=dirname, filename=f, last_edit=datetime.datetime.fromtimestamp(os.stat(fname).st_mtime))
            scraperscript.save()

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
    LoadReadings()
    MakeModels()


# functions used in scopesubmit

maineventfields = ["title", "summary", "url", "source", "refid", "quantity", "evt_time", "postcode", "lat", "lon", "district", ]

def AddUser(data):
    user_name = data.get("user_name")
    if not user_name or not re.match("[\w\d]+$", user_name):
        return "Bad user name"
    userswithname = models.ScopeUser.objects.filter(name=user_name)
    if userswithname:
        return "User name already used"
    user_password = data.get("user_password")
    if not user_password:
        return "Missing password"
    user_email = data.get("user_email")
    user = models.ScopeUser(name=user_name, password=user_password, email=user_email)
    user.save()
    return user     

def MatchEvent(data):
    rfmap = { }
    for rf in re.findall("\w+", data.get("non_replace_field", "")):
        if rf in maineventfields:
            rfval = data.get(rf)
            if rfval:
                rfmap[str(rf)] = str(rfval)
    if rfmap:
        return models.ScopeEvent.objects.filter(**rfmap)
    return []    

def MakeEvent(data):
    user_name = data.get("user_name")
    user_password = data.get("user_password")
    userswithname = models.ScopeUser.objects.filter(name=user_name, password=user_password)
    if not userswithname:
        return "No matching user"
    submitter = userswithname[0]

    rfmap = { "submitter":submitter, "sub_time":datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') }
    for rf in maineventfields:
        rfval = data.get(rf)
        if rfval:
            rfmap[rf] = rfval; 

    # need a function to convert postcode/district to lat lon    

    related_evtid = int(data.get("related_evt") or "0")
    if related_evtid:
        related_evts = models.ScopeEvent.objects.filter(id=related_evt)
        if related_evts:
            rfmap["related_evt"] = related_evts[0]
        

    if "title" not in rfmap or "url" not in rfmap:
        return "No title or url"

    event = models.ScopeEvent(**rfmap)
    event.save()
    return "event saved (" + str(event.id) + ")"

