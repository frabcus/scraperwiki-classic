import django.db
from django.db import models
from django.db import connection, backend, models
from django.db.models import Q
import settings
from collections import defaultdict
import re
import datetime
import types
from code import CodeManager
from datastore import  DataStore



class ScraperManager(CodeManager):
    #use_for_related_fields = True
    def __init__(self, *args, **kwargs):

        #datastore connection - these names seems to change based on the OS?
        backend = django.db.load_backend(settings.DATASTORE_DATABASE_ENGINE)
        self.datastore_connection = backend.DatabaseWrapper({
            'HOST': settings.DATASTORE_DATABASE_HOST,
            'NAME': settings.DATASTORE_DATABASE_NAME,
            'OPTIONS': {},
            'PASSWORD': settings.DATASTORE_DATABASE_PASSWORD,
            'PORT': settings.DATASTORE_DATABASE_PORT,
            'USER': settings.DATASTORE_DATABASE_USER,
            'TIME_ZONE': settings.TIME_ZONE,
            'DATABASE_HOST': settings.DATASTORE_DATABASE_HOST,
            'DATABASE_NAME': settings.DATASTORE_DATABASE_NAME,
            'DATABASE_OPTIONS': {},
            'DATABASE_PASSWORD': settings.DATASTORE_DATABASE_PASSWORD,
            'DATABASE_PORT': settings.DATASTORE_DATABASE_PORT,
            'DATABASE_USER': settings.DATASTORE_DATABASE_USER,
            'DATABASE_TIME_ZONE': settings.TIME_ZONE,
        })
        super(ScraperManager, self).__init__(*args, **kwargs)

    def get_query_set(self):
        return super(ScraperManager, self).get_query_set().filter(deleted=False)
        
            
    def owns(self):
        return self.get_query_set().filter(usercoderole__role='owner')
        
    def watching(self):
        return self.get_query_set().filter(usercoderole__role='follow')

    # returns a list of the users own scrapers that are currently good.
    def owned_good(self):
        good_ones = []
        for scraper in self.owns():
            if scraper.is_good():
                good_ones.append(scraper)
                
        return good_ones;

    def owned_count(self):
        return len(self.owns())
        
    def owned_good_count(self):
        return len(self.owned_good())   
        
    def watching_count(self):
        return len(self.watching())

    def not_watching_any(self):
        return self.watching_count() == 0

    def dont_own_any(self):
        return self.owned_count() == 0


    #for example lists
    def example_scrapers(self, user, count):
        scrapers = []
        if user.is_authenticated():
            scrapers = user.code_set.filter(usercoderole__role='owner', wiki_type='scraper', deleted=False, published=True)[:count]
        else:
            scrapers = self.filter(deleted=False, featured=True).order_by('first_published_at')[:count]
        
        return scrapers

    def emailer_for_user(self, user):
        try:
            queryset = self.get_query_set()
            queryset = queryset.filter(Q(usercoderole__role='owner') & Q(usercoderole__user=user))
            queryset = queryset.filter(Q(usercoderole__role='email') & Q(usercoderole__user=user))
            return queryset.latest('id')
        except:
            return None
