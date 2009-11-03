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


      # yuck, I have to build the database connection by hand
      backend = django.db.load_backend(settings.DATASTORE_DATABASE_ENGINE)
      connection = backend.DatabaseWrapper({
          'DATABASE_HOST': settings.DATASTORE_DATABASE_HOST,
          'DATABASE_NAME': settings.DATASTORE_DATABASE_NAME,
          'DATABASE_OPTIONS': {},
          'DATABASE_PASSWORD': settings.DATASTORE_DATABASE_PASSWORD,
          'DATABASE_PORT': settings.DATASTORE_DATABASE_PORT,
          'DATABASE_USER': settings.DATASTORE_DATABASE_USER,
          'TIME_ZONE': settings.TIME_ZONE,
      })

      data_sql = """
        SELECT * FROM (SELECT * FROM items LIMIT %(limit)s) as items
        JOIN kv
        ON items.item_id=kv.item_id
        WHERE items.scraper_id = '%(scraper_id)s'
        ORDER BY items.item_id, kv.key
      """ % locals()

      cursor = connection.cursor()
      cursor.execute(data_sql)


      rows = {}
      for row in cursor.fetchall():
          item_id = row[0]
          if not rows.has_key(item_id):
              rows[item_id] = {}
          rows[item_id][row[6]] = row[7]
      
      
      headings_sql = """
        SELECT `key` FROM kv 
        JOIN items 
        ON kv.item_id=items.item_id 
        WHERE items.scraper_id='%(scraper_id)s' 
        GROUP BY kv.key;
      """ % locals()
      
      cursor = connection.cursor()
      cursor.execute(headings_sql)
      
      
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
          print row


      # for i,row in rows.items():
      #     print row
      #     print ""
      #     print ""
      #     print ""
      #     print ""
      
      data = {
      'headings' : headings, 
      'rows' : rows,
      }
      
      
      
      return data
    