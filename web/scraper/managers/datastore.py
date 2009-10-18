import django.db
from django.db import models
from django.db import connection, backend, models
import settings
from collections import defaultdict

class datastore(models.Manager):

  def summary(self, scraper_id=0, limit=50):
    
    sql = """
      SELECT * FROM (SELECT * FROM items LIMIT 4) as items
      JOIN kv
      ON items.item_id=kv.item_id
    """
    
    
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
    
    cursor = connection.cursor()
    cursor.execute(sql)
    
    result_list = []
    rows = defaultdict(dict)
    for row in cursor.fetchall():
        item_id = row[0]
        rows[item_id][row[6]] = row[7]
          
        
    return dict(rows)
    
# import scraper
# scraper.models.scraperData.objects.summary()



