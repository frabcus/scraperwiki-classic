# encoding: utf-8
import datetime
import time
import tagging
import code
import scraper
import os
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from codewiki.managers.view import ViewManager

try:
    import json
except:
    import simplejson as json

class View (code.Code):

    mime_type = models.CharField(max_length=255, null=True)
    objects = ViewManager()    
    unfiltered = models.Manager() # django admin gets all confused if this lives in the parent class, so duplicated in child classes

    def __init__(self, *args, **kwargs):
        super(View, self).__init__(*args, **kwargs)
        self.wiki_type = 'view'        

    def save(self, *args, **kwargs):
        self.wiki_type = 'view'
        super(View, self).save(*args, **kwargs)

    def get_screenshot_url(self):
        return "http://www.google.co.uk"

    def get_screenshot_filename(self, size):
        filename = "%s_%s.png" % (self.short_name, size)
        return os.path.join(settings.VIEW_SCREENSHOT_DIR, filename)

    def content_type(self):
        return ContentType.objects.get(app_label="codewiki", model="View")

    class Meta:
        app_label = 'codewiki'


#register tagging
try:
    tagging.register(View)
except tagging.AlreadyRegistered:
    pass
