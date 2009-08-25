from django.db import models
from django.contrib import admin
from django.core.urlresolvers import reverse
import settings
import codecs
import os, urllib

class ScraperScript(models.Model):
    dirname     = models.CharField(max_length=200)   # readers|detectors
    filename    = models.CharField(max_length=200)
    modulename  = models.CharField(max_length=200)   # without the py
    last_edit   = models.DateTimeField(blank=True, null=True)
    last_run    = models.DateTimeField(blank=True, null=True)
    
    def __unicode__(self):
        return "%s/%s" % (self.dirname, self.filename)

    def get_codewiki_url(self):
        return reverse('codewikifile', kwargs={'dirname':self.dirname, 'filename':self.filename})
    
    def get_module(self, fromlist):
        # fromlist is the list of functions we want available
        return __import__("%s.%s" % (self.dirname, self.modulename), fromlist=fromlist)  
    
    class Meta:
        ordering = ('-last_edit',)


# a single scraped page here
class Reading(models.Model):
    scraper_tag = models.CharField(max_length=200)   # change to tag
    name        = models.CharField(max_length=200)
    url         = models.TextField()
    scrape_time = models.DateTimeField(blank=True, null=True)   # change to timescraped
    filepath    = models.CharField(max_length=200)
    submitter   = models.ForeignKey('ScraperScript', null=True) # not implemented
    mimetype    = models.CharField(max_length=40, blank=True)   # eg text/html 
    bytelength  = models.IntegerField()
    
    def __unicode__(self):
        return "%s: %s" % (self.name, self.url[:50])
    
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
    detector   = models.ForeignKey('ScraperScript') 
    reading    = models.ForeignKey('Reading') 
    result     = models.TextField()
    status     = models.CharField(max_length=40)
    
    
    
    
# copied from http://code.djangoproject.com/wiki/DynamicModels
# function for dynamic model creation
def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model

