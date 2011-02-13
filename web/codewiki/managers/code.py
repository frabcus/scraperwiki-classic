import django.db
from django.db import models
from django.db import connection, backend, models
import settings
from collections import defaultdict
import re
import datetime
import types
from tagging.utils import get_tag
from tagging.models import Tag, TaggedItem

from datastore import  DataStore


def convert_dictlist_to_datalist(allitems, column_order=None, private_columns=None):

    allkeys = set()
    for item in allitems:
        allkeys.update(item.keys())

    if type(column_order) == types.ListType and allkeys.issuperset(column_order):
        headings = column_order
    else:
        headings = sorted(list(allkeys))

    if type(private_columns) == types.ListType and set(headings).issuperset(private_columns):
        for column in private_columns:
            headings.remove(column)

    rows = [ ]
    for item in allitems:
        rows.append([ (key in item and unicode(item[key]) or "")  for key in headings ])
    
    return { 'headings' : headings, 'rows' : rows, }


class CodeManager(models.Manager):

    #use_for_related_fields = True

    def get_query_set(self):
        return super(CodeManager, self).get_query_set().filter(deleted=False)

        	
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

            # can't be used to access the new sqlite which requires short_names
            # questions the value of these functions all needing to take scraper_id when they could be members of Code
            # or simplified and in-lined
            
    def dataproxy(self, scraper_id):
        dataproxy = DataStore(scraper_id, "")  
        return dataproxy

    def data_search(self, scraper_id, key_values, limit=1000, offset=0):   
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.data_search(key_values, limit, offset)
        if not rc :
            raise Exception(arg)
        return arg

    def data_dictlist(self, scraper_id, short_name, tablename="", limit=1000, offset=0, start_date=None, end_date=None, latlng=None):
        dataproxy = DataStore(scraper_id, short_name)  
        rc, arg = dataproxy.data_dictlist(tablename, limit, offset, start_date, end_date, latlng)
        if not rc :
            raise Exception(arg)
        return arg
    
         # summary of old datasets (which should be merged in)
    def data_summary(self, scraper_id=0, limit=1000, offset=0, start_date=None, end_date=None, latlng=None, column_order=None, private_columns=None):
        allitems = self.data_dictlist(scraper_id, "", "", limit=limit, offset=offset, start_date=start_date, end_date=start_date, latlng=latlng)  
        return convert_dictlist_to_datalist(allitems, column_order, private_columns)

    def item_count(self, scraper_id):
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.item_count()
        if not rc :
            raise Exception(arg)
        return arg

    def has_geo(self, scraper_id):
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.has_geo()
        if not rc :
            raise Exception(arg)
        return arg

    def has_temporal(self, scraper_id):
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.has_temporal()
        if not rc :
            raise Exception(arg)
        return arg

            
            # used for the sparkline, so can go in a bit
    def recent_record_count(self, scraper_id, days):
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.recent_record_count(days)
        if not rc :
            raise Exception(arg)
        return arg
    
    
    
    def datastore_keys(self, scraper_id):

        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.datastore_keys()
        if not rc :
            raise Exception(arg)
        return arg

    def search(self, query):
        scrapers = self.get_query_set().filter(title__icontains=query, published=True)
        scrapers_description = self.get_query_set().filter(description__icontains=query, published=True)

        scrapers_all = scrapers | scrapers_description
        scrapers_all = scrapers_all.order_by('-created_at')

        return scrapers_all

