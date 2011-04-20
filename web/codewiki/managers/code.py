import django.db
from django.db import models
from django.db.models import Q
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

         # this is what the unfiltered objects is about
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


    def data_dictlist(self, scraper_id, short_name, tablename="", limit=1000, offset=0, start_date=None, end_date=None, latlng=None):
        dataproxy = DataStore(scraper_id, short_name)  
        rc, arg = dataproxy.data_dictlist(tablename, limit, offset, start_date, end_date, latlng)
        if rc:
            return arg
        
        # quick helper result for api when it searches on the default table (which is selected deep in the dataproxy after it has checked out the original mysql key-value datastore thing)
        if arg == "sqlite3.Error: no such table: main.swdata":
            sqlitedata = dataproxy.request(("sqlitecommand", "datasummary", 0, None))
            if sqlitedata and type(sqlitedata) not in [str, unicode]:
                return [{"error":arg}, {'datasummary':sqlitedata}]
        raise Exception(arg)
    
         # summary of old datasets (which should be merged in)
    def data_summary(self, scraper_id=0, limit=1000, offset=0, start_date=None, end_date=None, latlng=None, column_order=None, private_columns=None):
        allitems = self.data_dictlist(scraper_id, "", "", limit=limit, offset=offset, start_date=start_date, end_date=start_date, latlng=latlng)  
        return convert_dictlist_to_datalist(allitems, column_order, private_columns)


    def scraper_search_query(self, user, query):
        if query:
            scrapers = self.get_query_set().filter(title__icontains=query)
            scrapers_description = self.get_query_set().filter(description__icontains=query)
            scrapers_all = scrapers | scrapers_description
        else:
            scrapers_all = self.get_query_set()
        scrapers_all = scrapers_all.exclude(privacy_status="deleted")
        if user and not user.is_anonymous():
            scrapers_all = scrapers_all.exclude(Q(privacy_status="private") & ~(Q(usercoderole__user=user) & Q(usercoderole__role='owner')) & ~(Q(usercoderole__user=user) & Q(usercoderole__role='editor')))
        else:
            scrapers_all = scrapers_all.exclude(privacy_status="private")
        scrapers_all = scrapers_all.order_by('-created_at')
        return scrapers_all

