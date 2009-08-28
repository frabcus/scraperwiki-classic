import sys
submiturl = None # = "http://127.0.0.1:8010/scope/submit"
import os
import settings 
from django.core import management
from django.db import connection
import codewiki.models as models
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
    
def SaveScraping(scraper_tag, name, url, text, timestamp=None):
    if timestamp:
        readings = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
        #readings.delete()
        #readings = []
        if readings:
            reading = readings[0]
            if reading.scrape_time >= timestamp:
                if reading.scrape_time == timestamp:
                    if reading.contents() != text:
                        print "Mismatch text " + str(timestamp), len(reading.contents()), len(text)
                        assert False
                return reading
        scrape_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        scrape_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    reading = models.Reading(scraper_tag=scraper_tag, name=name, url=url, scrape_time=scrape_time)
    reading.mimetype = "text/html"   # should come from the scrape function
    reading.bytelength = len(text)
    reading.save()   # to make the id for the filepath
    reading.filepath = os.path.join(settings.READINGS_DIR, "%d%s" % (reading.id, reading.fileext()))
    reading.SaveReading(text)
    reading.save()
    print "Saved:", reading
    return reading


def ScrapeCachedURL(scraper_tag, name, url, params=None, bforce=False):
    readings = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
    if not readings or bforce:
        text = ScrapeURL(url=url, params=params)
        SaveScraping(scraper_tag=scraper_tag, name=name, url=url, text=text)    
        readings = models.Reading.objects.filter(scraper_tag=scraper_tag, name=name).order_by('-scrape_time')
        assert readings
    return readings[0].contents()
    

def ListWikipediaDumps():
    return [os.path.join(settings.SCRAPERWIKI_DIR, "wikipediadumps", f)  \
            for f in os.listdir(os.path.join(settings.SCRAPERWIKI_DIR, "wikipediadumps"))  \
            if f[-4:] == ".xml"]
#
# submitting utils
#




#
# the execution and iteration between detectors and readings
#

# gets all output from detectors
# should be removed
def GetDetectings(detectorname):
    detector = __import__(detectorname, fromlist=["DoesApply", "Parse"])  # have to tell it which functions we want, when the import has a . in it
    for reading in models.Reading.objects.all():
        if detector.DoesApply(reading):
             for keyvalues in detector.Parse(reading):
                 yield keyvalues
            



# this is immediate execution of script that outputs the values when viewing a detector
if __name__ == "__main__":
    if sys.argv[1] == "DoesApplyAll":
        detector = models.ScraperScript.objects.get(dirname="detectors", modulename=sys.argv[2])
        detector.detection_set.all().delete()
        detectormodule = detector.get_module(["DoesApply"])
        for reading in models.Reading.objects.all():
            if detectormodule.DoesApply(reading):
                detection = models.Detection(detector=detector, reading=reading, status="doesapply")
                detection.save()
                print '<a href="?pageid=%s">%s</a>' % (reading.id, reading)

    if sys.argv[1] == "ParseSingle":
        detector = models.ScraperScript.objects.get(dirname="detectors", modulename=sys.argv[2])
        reading = models.Reading.objects.get(id=sys.argv[3])
        detection = models.Detection.objects.get(detector=detector, reading=reading)
        detectormodule = detector.get_module(["Parse"])
        print 'Parsing <a href="/reading/%s">%s</a>' % (reading.id, reading)
        keyvaluelist = list(detectormodule.Parse(detection.reading))
        detection.result = keyvaluelist.__repr__()
        detection.status = "parsed"
        detection.save()
        i = 0
        for keyvaluelist in detectormodule.Parse(reading):
            print i, keyvaluelist
            i += 1

    if sys.argv[1] == "ParseAll":
        detector = models.ScraperScript.objects.get(dirname="detectors", modulename=sys.argv[2])
        detectormodule = detector.get_module(["Parse"])
        for detection in detector.detection_set.all():
            print '<a href="?pageid=%s">%s</a>' % (detection.reading.id, detection.reading)
            keyvaluelist = list(detectormodule.Parse(detection.reading))
            detection.result = keyvaluelist.__repr__()
            detection.status = "parsed"
            detection.save()
            print detection.result

    if sys.argv[1] == "MakeModel":
        print "sssss"
        detector = models.ScraperScript.objects.get(dirname="collectors", modulename=sys.argv[2])
        detectormodule = detector.get_module(["MakeModels"])
        detectormodule.MakeModels()


