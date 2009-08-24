from django.db import models
from django.contrib import admin
from django.core.urlresolvers import reverse
import settings
import codecs

class ScraperScript(models.Model):
    dirname     = models.CharField(max_length=200)   # readers|detectors
    filename    = models.CharField(max_length=200)
    last_edit   = models.DateTimeField(blank=True, null=True)
    last_run    = models.DateTimeField(blank=True, null=True)
    
    #modulename  = models.CharField(max_length=200) # same as filename, but without the .py
    
    class Meta:
        ordering = ('dirname','filename')  
    
    def __unicode__(self):
        return "%s/%s" % (self.dirname, self.filename)

    def get_codewiki_url(self):
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
    submitter   = models.ForeignKey('ScraperScript', null=True)
    mimetype    = models.CharField(max_length=40, blank=True)   # eg text/html 
    bytelength  = models.IntegerField()
    
    def __unicode__(self):
        return "%s:%s" % (self.name, self.url[:50])
    
    def contents(self):
        fin = open(self.filepath)
        text = fin.read(self.bytelength)
        fin.close()
        return text

    def fileext(self):
        if self.mimetype == "text/html":
            return ".html"
        assert False
        return ""

    # copy save and load reading into here and get the text left on the disk
    def SaveReading(self, text):
        assert self.mimetype == "text/html"
        self.filepath = os.path.join(settings.READINGS_DIR, "%d%s" % (self.id, self.fileext()))
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

