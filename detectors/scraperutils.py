import sys
submiturl = None # = "http://127.0.0.1:8010/scope/submit"
import os
import settings 
from django.core import management
from django.db import connection
import codewiki.models as models
from codewiki.postdata import MakeEvent, MatchEvent, AddUser
from django.core.urlresolvers import reverse


# also fixed value

import urllib2, cookielib, urllib
import re
import datetime

#
# text searching utils
#
def redfindone(c, text):
    res = re.findall(c, text)
    assert len(res) == 1, (c, text)
    return res[0]

def redfindonez(c, text):
    if not text:
        return ""
    res = re.findall(c, text)
    assert len(res) <= 1, (c, text)
    return res and res[0] or ""

def cleanhtmltags(text):
    res = re.sub("<[^>]*>", " ", text or "")
    res = re.sub("&nbsp;", " ", res)
    res = re.sub("&hellip;", "...", res)
    res = re.sub("\s+", " ", res)
    return res.strip()


#
# scraping utils 

cj = cookielib.CookieJar()
urllibopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    
def ScrapeURL(url, params=None):
    data = params and urllib.urlencode(params) or None
    fin = urllibopener.open(url, data)
    text = unicode(fin.read(), errors="replace").encode("ascii", "ignore")
    fin.close()   # get the mimetyle here
    print "Scraped: %d bytes from %s" % (len(text), url[:30])
    return text
    
def SaveScraping(scraper_tag, name, url, text):
    scrape_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reading = models.Reading(scraper_tag=scraper_tag, name=name, url=url, scrape_time=scrape_time)
    reading.mimetype = "text/html"   # should come from the scrape function
    text = text.encode("ascii", "ignore")  # original text
    reading.SaveReading(text)
    reading.save()
    print reading
    return text

def FetchCorrectedText(scraper_tag, name):
    stexts = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
    if stexts:
        return stexts[0].gettext(), stexts[0].url
    return "", ""

def ScrapeCachedURL(scraper_tag, name, url, params=None, bforce=False):
    readings = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
    if not readings or bforce:
        text = ScrapeURL(url=url, params=params)
        SaveScraping(scraper_tag=scraper_tag, name=name, url=url, text=text)    
        readings = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
        assert readings
    return readings[0].gettext()
    
def FetchNames(scraper_tag):
    res = set()
    for stext in models.Reading.objects.filter(scraper_tag=scraper_tag):
        res.add(stext.name)
    res = list(res)
    res.sort()
    return res

def ListWikipediaDumps():
    return [os.path.join(settings.CODEWIKI_DIR, "wikipediadumps", f)  \
            for f in os.listdir(os.path.join(settings.CODEWIKI_DIR, "wikipediadumps"))  \
            if f[-4:] == ".xml"]
#
# submitting utils
#

def CreateScopeUser(user_name, user_password, user_email):
    data = {"user_name":user_name, "user_password":user_password, "user_email":user_email}
    urlout = settings.SUBMIT_URL + "?" + urllib.urlencode(data)
    print urlout
    fout = urllib2.urlopen(urlout)
    print fout.read()
    fout.close()

def PostDataRemote(data):
    urlout = settings.SUBMIT_URL + "?" + urllib.urlencode(data)
    fout = urllib2.urlopen(urlout)
    res = fout.read()
    fout.close()
    bsucc = re.search("Thanks", res)
    return bsucc

def PostData(data):
    if data.get("user_email"):
        message = AddUser(data)
        return message

    mevts = MatchEvent(data)
    if mevts:
        message = "Matching events already there: " + str(mevts)
        models.ScopeEvent.delete(mevts[0])
        MakeEvent(data)  # over-write
    else:
        message = MakeEvent(data)
    return message


#
# the execution and iteration between detectors and readings
#

# gets all output from detectors
def GetDetectings(detectorname):
    detector = __import__(detectorname, fromlist=["DoesApply", "Parse"])  # have to tell it which functions we want, when the import has a . in it
    for reading in models.Reading.objects.all():
        if detector.DoesApply(reading):
             for keyvalues in detector.Parse(reading):
                 yield keyvalues
            

# this is immediate execution of script that outputs the values when viewing a collector
if __name__ == "__main__":
    if sys.argv[1] == "DoesApply":
        detector = __import__(sys.argv[2], fromlist=["DoesApply"])  # have to tell it which functions we want, when the import has a . in it
        for reading in models.Reading.objects.all():
            if detector.DoesApply(reading):
                print '<a href="?pageid=%s">%s</a>' % (reading.id, reading)

    # should be entered into the database and stored
    if sys.argv[1] == "Parse":
        detector = __import__(sys.argv[2], fromlist=["Parse"])  # have to tell it which functions we want, when the import has a . in it
        reading = models.Reading.objects.get(id=sys.argv[3])
        print 'Parsing <a href="/reading/%s">%s</a>' % (reading.id, reading)
        i = 0
        for keyvaluelist in detector.Parse(reading):
            print i, keyvaluelist
            i += 1


