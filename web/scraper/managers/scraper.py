import django.db
from django.db import models
from django.db import connection, backend, models
import settings
from collections import defaultdict
import re


def convert_dictlist_to_datalist(allitems):
    allkeys = set()
    for item in allitems:
        allkeys.update(item.keys())
    
    headings = sorted(list(allkeys))
    rows = [ ]
    for item in allitems:
        rows.append([ (key in item and unicode(item[key]) or "")  for key in headings ])
    
    return { 'headings' : headings, 'rows' : rows, }


class ScraperManager(models.Manager):
    """
        This manager is implemented to allow you to link back to the particular scrapers through
        names defining their relationship to the user.

        So, having a user

        > user

        you can reference all scrapers that user has ownership of by

        > user.scraper_set.owns()

        and you can reference all the scrapers that user is watching by

        > user.scraper_set.watching()

        to check if this user owns any scrapers you can use

        > user.dont_own_any()

        or to check if the user is following any

        > user.not_watching_any()

    """
    
    def __init__(self, *args, **kwargs):

        
        # yuck, I have to build the database connection by hand
        backend = django.db.load_backend(settings.DATASTORE_DATABASE_ENGINE)
        self.datastore_connection = backend.DatabaseWrapper({
            'DATABASE_HOST': settings.DATASTORE_DATABASE_HOST,
            'DATABASE_NAME': settings.DATASTORE_DATABASE_NAME,
            'DATABASE_OPTIONS': {},
            'DATABASE_PASSWORD': settings.DATASTORE_DATABASE_PASSWORD,
            'DATABASE_PORT': settings.DATASTORE_DATABASE_PORT,
            'DATABASE_USER': settings.DATASTORE_DATABASE_USER,
            'TIME_ZONE': settings.TIME_ZONE,
        })
        super(ScraperManager, self).__init__(*args, **kwargs)
    
    use_for_related_fields = True
	
    def owns(self):
        return self.get_query_set().filter(userscraperrole__role='owner')
		
    def watching(self):
        return self.get_query_set().filter(userscraperrole__role='follow')

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

            
    # this accesses the tables defined in scraperlibs/scraperwiki/datastore/scheme.sql and accessed in datastore/save.py
    def data_dictlist(self, scraper_id, limit=1000, offset=0, start_date=None, end_date=None, latlng=None):   
        '''map from scraper_id and filters to dict representing row record for a particular scraper'''
        
        # previously implemented with a sub-select table joined on kv.  
        # Now implemented by fetching the items, and building each row separately
        
        # split the latlng into a pair
        if latlng:
            latlng = tuple(map(float, latlng.split(",")))

        # code here similar to datastore/save.py __build_matches
        
        qquery = ["SELECT items.item_id AS item_id"]
        qquery.append("FROM items")
        qlist  = [ ]
        if latlng:
            qquery.append(", items.latlng AS latlng")
        
        # filter on a key existing and value being the same in the data for the record, using INNER JOIN (see datastore.save.__build_matches)
        #     (not yet used feature)
        filterkey=None
        filtervalue=None
        if filterkey:
            qquery.append("INNER JOIN")
            qquery.append("kv AS kv0")
            qquery.append("ON")
            qquery.append("kv0.item_id=items.item_id")
            qquery.append("AND")
            qquery.append("kv0.key=%s")
            qlist.append(filterkey)
            if filtervalue:
                qquery.append("AND")
                qquery.append("kv0.value=%s")
                qlist.append(filtervalue)

        # add the where clause
        qquery.append("WHERE items.scraper_id=%s")
        qlist.append(scraper_id)
        
        # filter by latlng exists; (can't filter by distance with this object!)
        if latlng:
            qquery.append("AND items.latlng IS NOT NULL")
        
        if start_date and end_date:
            #qquery.append("AND items.`date` IS NOT NULL")
            qquery.append("AND items.`date` >= %s")
            qlist.append(start_date)
            qquery.append("AND items.`date` < %s")
            qlist.append(end_date)
        
        #if latlng:
        #    qquery.append("ORDER BY items.item_id")
        #else:
        qquery.append("ORDER BY items.item_id")
        #if locationpoint:   # don't have capability to do this yet
        #    qquery.append("ORDER BY DIST(latlng, locationpoint)")
        
        qquery.append("LIMIT %s")
        #qlist.append(offset)
        qlist.append(2)
      
        print " ".join(qquery), qlist
        c = self.datastore_connection.cursor()
        
        c.execute(" ".join(qquery), tuple(qlist))
        item_idlist = c.fetchall()
        
        # code here similar to datastore/save.py __retrieve_item
        
        allitems = [ ]
        for item_idl in item_idlist:
            item_id = item_idl[0]
            
            rdata = { }
            
            # header records
            if not c.execute("SELECT `date`, latlng, `date_scraped` FROM items WHERE item_id=%s", (item_id,)):
                continue  # shouldn't happen
            item = c.fetchone()
            
            if item[0]:
                rdata["date"] = item[0]
            if item[1]:
                rdata["latlng"] = item[1]
                latlng = map(float, item[1].split(","))
            if item[2]:
                rdata["date_scraped"] = item[2]
                        
            # put the key values in
            c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
            for key, value in c.fetchall():
                rdata[key] = value
        
            allitems.append(rdata)
        return allitems
           
              
              
              
    
    def data_summary(self, scraper_id=0, limit=1000, offset=0, start_date=None, end_date=None, latlng=None):
        '''single table of all rows for a scraper'''
        allitems = self.data_dictlist(scraper_id, limit=limit, offset=offset, start_date=start_date, end_date=start_date, latlng=latlng)  
        return convert_dictlist_to_datalist(allitems)
      


    # not yet used   probably to delete
    def data_summary_tables(self, scraper_id=0, limit=1000):
      '''multiple table of rows for a scraper, indexed by the __table key'''
      allitems = self.__data_summary_map(scraper_id, limit)
            
      alltables = set()
      for item in allitems.values():
        alltables.add(item.get("__table"))
      
      data_tables = { }
      
      # filter for each table in order; not efficient, but simple
      for table in alltables:
        allkeys = set()
        for item in allitems.values():
          if item.get("__table") == table:
            allkeys.update(item.keys())
        
        headings = sorted(list(allkeys))
        rows = [ ]
        for item in allitems.values():
          if item.get("__table") == table:
            rows.append([ unicode(item.get(key))  for key in headings ])

        data_tables[table] = { 'headings' : headings, 'rows' : rows }
      return data_tables
          

    def item_count(self, guid):
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id='%s'" % guid
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0]

    def item_count_for_tag(self, guids):  # to delete
        guids = ",".join("'%s'" % guid for guid in guids)
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id IN (%(guids)s)" % locals()
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0]
        
        