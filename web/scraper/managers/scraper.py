import django.db
from django.db import models
from django.db import connection, backend, models
import settings
from collections import defaultdict


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


    def __data_summary_map(self, scraper_id=0, limit=1000):   # should remove the defaults and disable limit if 0
      '''map from scraper_id to dict representing row record for a particular scraper'''
      if isinstance(scraper_id, list):
          guids = ",".join("'%s'" % guid for guid in scraper_id)
      else:
          guids = "'%s'" % scraper_id

      cursor = self.datastore_connection.cursor()
      cursor.execute("""
          SELECT items.`item_id` AS item_id, `date_scraped`, 
                 kv.`key` AS `key`, kv.`value` AS `value`
          FROM (SELECT * FROM items WHERE items.scraper_id IN (%(guids)s) LIMIT %(limit)s) as items
          LEFT JOIN kv
             ON items.item_id=kv.item_id
          ORDER BY items.item_id, items.date_scraped
        """ % locals())
      
      allitems = { }
      currentitem = None
      for row in cursor.fetchall():
          item_id = row[0]
          
          # item_id changes; start new object
          if item_id not in allitems:
              currentitem = { "date_scraped":row[1] }
              allitems[item_id] = currentitem
          
          # add the value in if the key exists
          key = row[2]
          if key:    
              currentitem[key] = row[3]
      
      return allitems
           
              
    def data_summary(self, scraper_id=0, limit=1000):
      '''single table of all rows for a scraper'''
      allitems = self.__data_summary_map(scraper_id, limit)
      
      allkeys = set()
      for item in allitems.values():
        allkeys.update(item.keys())
        
      headings = sorted(list(allkeys))
      rows = [ ]
      for item in allitems.values():
        rows.append([ unicode(item.get(key))  for key in headings ])
      
      data = {
      'headings' : headings, 
      'rows' : rows,
      }
      
      return data

    # not yet used
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

    # Is the idea to use tags to aggregate data from different scrapers?  assumes too much for their consistency.  
    # This explains the idea of allowing multiple guids.  
    # I think this is being very optimistic.  It really will require collector-scrapers to make the fields consistent, 
    # because the fields from one dataset should be according to the terminology of that dataset source, 
    # because this is not going to continually change with the fashion.  --JT
    def item_count_for_tag(self, guids):
        guids = ",".join("'%s'" % guid for guid in guids)
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id IN (%(guids)s)" % locals()
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0]
        
        