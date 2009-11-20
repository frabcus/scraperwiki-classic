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


    def data_summary(self, scraper_id=0, limit=1000):
      
      if isinstance(scraper_id, list):
          guids = ",".join("'%s'" % guid for guid in scraper_id)
      else:
          guids = "'%s'" % scraper_id

      cursor = self.datastore_connection.cursor()
      cursor.execute("""
          SELECT * FROM 
            (SELECT * 
             FROM items 
             WHERE items.scraper_id IN (%(guids)s) 
             LIMIT %(limit)s
             ) as items
          JOIN kv
          ON items.item_id=kv.item_id
          ORDER BY items.date_scraped, items.item_id, kv.key
        """ %  locals())

      rows = {}
      for row in cursor.fetchall():
          item_id = row[0]
          if not rows.has_key(item_id):
              rows[item_id] = {}
          rows[item_id][row[7]] = row[8]

      cursor = self.datastore_connection.cursor()
      cursor.execute("""
      SELECT `key` FROM kv 
      JOIN items 
      ON kv.item_id=items.item_id 
      WHERE items.scraper_id IN (%(guids)s) 
      GROUP BY kv.key;
      """ % {'guids' : guids})
      
      
      headings = []
      for row in cursor.fetchall():
          headings.append(row[0])


      
      for item_id,row in rows.items():
          for heading in headings:
              if not row.has_key(heading):
                  row[heading] = ""
          
          items = row.items()
          items.sort()
          rows[item_id] = [value for key, value in items]
      
      data = {
      'headings' : headings, 
      'rows' : rows,
      }
      
      return data





    def item_count(self, guid):
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id='%s'" % guid
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0]

    def item_count_for_tag(self, guids):
        guids = ",".join("'%s'" % guid for guid in guids)
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id IN (%(guids)s)" % locals()
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()[0]
        