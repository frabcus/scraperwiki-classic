# encoding: utf-8
import datetime
import time

from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
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

SCHEDULE_OPTIONS = ((-1, 'never'), (3600*24, 'once a day'), (3600*24*2, 'every two days'), (3600*24*3, 'every three days'),                                                                 (3600*24*7, 'once a week'), (3600*24*14, 'every two weeks'), (3600*24*31, 'once a month'), (3600*24*63, 'every two months'), (3600*24*182, 'every six months'),)
SCHEDULE_OPTIONS_DICT = dict(SCHEDULE_OPTIONS)

class Scraper (code.Code):

    has_geo      = models.BooleanField(default=False)
    has_temporal = models.BooleanField(default=False)    
    last_run     = models.DateTimeField(blank=True, null=True)    
    license      = models.CharField(max_length=100, blank=True)
    license_link = models.URLField(verify_exists=False, null=True, blank=True)
    record_count = models.IntegerField(default=0)        
    scraper_sparkline_csv = models.CharField(max_length=255, null=True)
    run_interval = models.IntegerField(default=86400)  # in seconds

    objects = managers.scraper.ScraperManager()
    unfiltered  = models.Manager() # django admin gets confused if this lives in the parent class, so duplicated in child classes

    def __init__(self, *args, **kwargs):
        super(Scraper, self).__init__(*args, **kwargs)
        self.wiki_type = 'scraper'
        self.license = 'Unknown'

    def clean(self):
        if self.run_interval == 'draft' and self.pub_date is not None:
            found = False
            for schedule_option in SCHEDULE_OPTIONS:
                if schedule_option[0] == self.run_interval:
                    found = True
            if not found:
                raise ValidationError('Invalid run interval')

        
    def count_records(self):
        return int(Scraper.objects.item_count(self.guid))


    # update scraper meta data (lines of code etc)    
    def update_meta(self):

        # runs Code.update_meta
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

    def content_type(self):
        return ContentType.objects.get(app_label="codewiki", model="Scraper")

    # perhaps should be a member variable so we can sort directly on it (and set it when we want something to run immediately)
    def next_run(self):
        if not self.run_interval:
            return datetime.datetime(9999, 12, 31)
        if not self.last_run:
            return datetime.datetime.now() - datetime.timedelta(1, 0, 0)  # one day ago
        return self.last_run + datetime.timedelta(0, self.run_interval, 0)


    class Meta:
        app_label = 'codewiki'

        
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
        app_label = 'codewiki'
        verbose_name_plural = 'scraper metadata'

class ScraperRunEvent(models.Model):
    scraper         = models.ForeignKey(Scraper)
    run_id          = models.CharField(max_length=100)  
    pid             = models.IntegerField()   # will only be temporarily valid and probably doesn't belong here
    run_started     = models.DateTimeField()
    run_ended       = models.DateTimeField(null=True)
    records_produced = models.IntegerField(default=0)
    pages_scraped   = models.IntegerField(default=0)
    output          = models.TextField()

    def __unicode__(self):
        return u'start: %s   end: %s' % (self.run_started, self.run_ended)

    @models.permalink
    def get_absolute_url(self):
        return ('run_event', [self.id])

    class Meta:
        app_label = 'codewiki'
