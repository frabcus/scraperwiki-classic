from django.db import models
from django.contrib import admin
from django.core.urlresolvers import reverse
import settings
import codecs
import os, urllib
from django.core.management import sql, color
from django.db import connection
import settings
import re
import datetime
from BeautifulSoup import BeautifulSoup

class ScraperModule(models.Model):
    modulename  = models.CharField(max_length=200)
    last_run    = models.DateTimeField(blank=True, null=True)
    
    def __unicode__(self):
        return "module: %s" % (self.modulename)

    def get_module(self, fromlist):
        # fromlist is the list of functions we want available
        return __import__("scrapers." + self.modulename, fromlist=fromlist)  
    
    def last_edit(self):
        edits = [f.last_edit  for f in self.scraperfile_set.all() ]
        return edits and max(edits) or ""
    
    class Meta:
        ordering = ('-last_run',)


class ScraperFile(models.Model):
    module      = models.ForeignKey('ScraperModule') 
    filename    = models.CharField(max_length=200)
    last_edit   = models.DateTimeField(blank=True, null=True)
    
    def __unicode__(self):
        return "file: %s/%s" % (self.module.modulename, self.filename)

    def contents(self):
        ffname = os.path.join(settings.SMODULES_DIR, self.module.modulename, self.filename)
        fin = open(ffname, "r")
        res = fin.read()
        fin.close()
        return res
    
    def SaveFile(self, text):
        ffname = os.path.join(settings.SMODULES_DIR, self.module.modulename, self.filename)
        fout = open(ffname, "w")
        fout.write(text)
        fout.close()
        self.last_edit = datetime.datetime.fromtimestamp(os.stat(ffname).st_mtime)
        self.save()
    
    def Dget_codewiki_url(self):
        return reverse('codewikifile', kwargs={'dirname':self.dirname, 'filename':self.filename})
            
    class Meta:
        ordering = ('-last_edit',)


# a single scraped page here
class Reading(models.Model):
    scraper_tag = models.CharField(max_length=200)   # change to tag
    name        = models.CharField(max_length=200)
    url         = models.TextField()
    scrape_time = models.DateTimeField(blank=True, null=True)   # change to timescraped
    filepath    = models.CharField(max_length=200)
    submitter   = models.ForeignKey('ScraperModule', null=True) # not implemented
    mimetype    = models.CharField(max_length=40, blank=True)   # eg text/html 
    bytelength  = models.IntegerField()
    
    def __unicode__(self):
        return "%s: %s" % (self.name, self.url[:50])
    
    def contents(self):
        fin = open(self.filepath)
        text = fin.read(self.bytelength)
        fin.close()
        return text

    def soup(self):
        return BeautifulSoup(self.contents())

    def fileext(self):
        if self.mimetype == "text/html":
            return ".html"
        assert False
        return ""

    # copy save and load reading into here and get the text left on the disk
    def SaveReading(self, text):
        assert self.mimetype == "text/html"
        fout = open(self.filepath, "w")
        fout.write(text)
        tailvals = [ ("name", self.name), ("scraper_tag", self.scraper_tag), ("url", self.url), ("scrape_time", self.scrape_time), ("id", self.id),  ("mimetype", self.mimetype) ]
        tail = [ ]
        for k, v in tailvals:
            tail.append("\n  <<<%s=%s>>>  " % (k, urllib.quote(str(v))))
        tailstring = "".join(tail)
        fout.write(tailstring)
        fout.write("tailleng=%09d" % len(tailstring))  # used to count back from end of page and get rid of the parameter section
        fout.close()

# the cross product of Detectors and Readings
class Detection(models.Model):
    scraper    = models.ForeignKey('ScraperModule', null=True) 
    reading    = models.ForeignKey('Reading') 
    result     = models.TextField()
    status     = models.CharField(max_length=40)
    
    def contents(self):
        return eval(self.result)
    
    

# these don't work, but I would like them to be the basis of user generated models
class DynamicModel(models.Model):
    new_since_parsing = models.BooleanField(default=False, editable=False)
    non_public = models.BooleanField(default=False)

    #class Meta:
	#    abstract = True
    
    
#
# these to go in the app that is a single scraper module
# made dynamically!!!
#
class DynElection(DynamicModel):
    election     = models.CharField(max_length=200)
    year         = models.CharField(max_length=20)
    candidate    = models.CharField(max_length=200, blank=True)
    party        = models.CharField(max_length=200)
    votes        = models.IntegerField()
    winner       = models.BooleanField()
    constituency = models.CharField(max_length=200)
    source       = models.CharField(max_length=200)  # wikipedia or partyweb
    
class DynPartyCandidate(DynamicModel):
    candidaterow = models.ForeignKey("DynElection")
    urlsource    = models.CharField(max_length=400)  # could be a Reading
    email        = models.CharField(max_length=200)
    web          = models.CharField(max_length=200)
    phone        = models.CharField(max_length=200)
    address      = models.CharField(max_length=400)


# http://code.djangoproject.com/wiki/DynamicModels
# http://www.adoleo.com/blog/2008/nov/21/djangos-dynamic-urls/
# Django 1.1  Definitive Guide to Django Done Right   Holovaty 1.1
# graphiviz
# jinja   http://jinja.pocoo.org/2/documentation/templates
# flotr   mathplot
# lamptraining.com
# http://matplotlib.sourceforge.net/
