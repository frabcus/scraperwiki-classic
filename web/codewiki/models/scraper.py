# encoding: utf-8
import datetime
import time

from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
import settings

import codewiki.managers.scraper
from codewiki import managers
from django.db.models.signals import post_save
from registration.signals import user_registered

import tagging
from frontend import models as frontendmodels

import codewiki.util
import codewiki.vc
import code
import view

try:
    import json
except:
    import simplejson as json

from django.core.mail import send_mail

class Scraper (code.Code):

    has_geo = models.BooleanField(default=False)
    has_temporal = models.BooleanField(default=False)    
    last_run = models.DateTimeField(blank=True, null=True)    
    license = models.CharField(max_length=100, blank=True)
    record_count = models.IntegerField(default=0)        
    scraper_sparkline_csv = models.CharField(max_length=255, null=True)
    run_interval = models.IntegerField(default=86400)

    objects = managers.scraper.ScraperManager()
    unfiltered = models.Manager() # django admin gets all confused if this lives in the parent class, so duplicated in child classes

    def __init__(self, *args, **kwargs):
        super(Scraper, self).__init__(*args, **kwargs)
        self.wiki_type = 'scraper'
        self.license = 'Unknown'        
        
    def count_records(self):
        return int(Scraper.objects.item_count(self.guid))


    # update scraper meta data (lines of code etc)    
    def update_meta(self):

        #run parent's update_meta method
        super(Scraper, self).update_meta()

        #update line counts etc
        self.record_count = self.count_records()
        self.has_geo = bool(Scraper.objects.has_geo(self.guid))
        self.has_temporal = bool(Scraper.objects.has_temporal(self.guid))

        #get data for sparklines
        sparkline_days = settings.SPARKLINE_MAX_DAYS
        created_difference = datetime.datetime.now() - self.created_at

        if (created_difference.days < settings.SPARKLINE_MAX_DAYS):
            sparkline_days = created_difference.days

        #minimum of 1 day
        recent_record_count = Scraper.objects.recent_record_count(self.guid, sparkline_days)
        self.scraper_sparkline_csv = ",".join("%d" % count for count in recent_record_count)

    def save(self, *args, **kwargs):
        self.wiki_type = 'scraper'
        super(Scraper, self).save(*args, **kwargs)

        
#register tagging for scrapers
try:
    tagging.register(Scraper)
except tagging.AlreadyRegistered:
    pass
    


class ScraperMetadata(models.Model):
    """
    Allows named metadata to be associated with a scraper
    """
    name = models.CharField(max_length=100, null=False, blank=False)
    scraper = models.ForeignKey(Scraper, null=False)
    run_id = models.CharField(max_length=100, null=False, blank=False)
    value = models.TextField()

    def __unicode__(self):
        return u"%s['%s']" % (self.scraper, self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('metadata_api', [self.scraper.guid, self.name])

    class Meta:
        verbose_name_plural = 'scraper metadata'

class ScraperRunEvent(models.Model):
    scraper = models.ForeignKey(Scraper)
    run_id = models.CharField(max_length=100)
    pid = models.IntegerField()
    run_started = models.DateTimeField()
    run_ended = models.DateTimeField(null=True)
    records_produced = models.IntegerField(default=0)
    pages_scraped = models.IntegerField(default=0)
    output = models.TextField()

    def __unicode__(self):
        return u'start: %s   end: %s' % (self.run_started, self.run_ended)

    @models.permalink
    def get_absolute_url(self):
        return ('run_event', [self.id])
