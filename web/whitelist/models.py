from django.db import models
from django.contrib.auth.models import User
from django.template import loader, Context
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


class Whitelist(models.Model):
    """
        Site wide Whitelist and blacklists to be supplied to proxy
    """
    URLCOLOUR_CHOICES = ( ("white", "white"), ("black", "black") )
    
    urlregex  = models.CharField(max_length = 200)
    urlcolour = models.CharField(max_length = 50, choices=URLCOLOUR_CHOICES)    
    urlregexname = models.CharField(max_length = 200, blank=True)
    
    def __unicode__(self):
        return self.urlregex

