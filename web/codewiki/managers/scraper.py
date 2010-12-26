import django.db
from django.db import models
from django.db import connection, backend, models
import settings
from collections import defaultdict
import re
import datetime
import types
from code import CodeManager
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

    def dataproxy(self, scraper_id):
        dataproxy = DataStore(scraper_id)
        return dataproxy

    def clear_datastore(self, scraper_id):
        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.clear_datastore()
        if not rc :
            raise Exception(arg)

    def datastore_keys(self, scraper_id):

        result = []
        c = self.datastore_connection.cursor()
        c.execute("select distinct kv.key from items inner join kv on kv.item_id=items.item_id WHERE items.scraper_id=%s", (scraper_id,))        
        keys = c.fetchall()
        for key in keys:
            result.append(key[0])

        c.close()
        return result

    def data_search(self, scraper_id, key_values, limit=1000, offset=0):   

        qquery = ["SELECT items.item_id, COUNT(items.item_id) as item_count"]
        qlist  = [ ]

        qquery.append("FROM items")
        qquery.append("inner join kv on items.item_id = kv.item_id")

        # add the where clause
        qquery.append("WHERE items.scraper_id=%s")
        qlist.append(scraper_id)

        filters = []
        for key_value in key_values:
            filters.append("(kv.key = %s and kv.value = %s)")
            qlist.append(key_value[0])
            qlist.append(key_value[1])

        qquery.append("AND (%s)" % " OR ".join(filters))

        qquery.append("GROUP BY items.item_id")

        qquery.append("HAVING item_count = %s")
        qlist.append(len(key_values))
        
        qquery.append("LIMIT %s,%s")
        qlist.append(offset)
        qlist.append(limit)

        #execute
        c = self.datastore_connection.cursor()
        c.execute(" ".join(qquery), tuple(qlist))
        item_idlist = c.fetchall()

        allitems = [ ]
        for item_idl in item_idlist:

            #get the item ID and create an object for the data to live in
            item_id = item_idl[0]
            rdata = { }

            #add distance if present
            if len(item_idl) > 1:
                rdata['distance'] = item_idl[1]

            # header records
            if not c.execute("SELECT `date`, latlng, `date_scraped` FROM items WHERE item_id=%s", (item_id,)):
                continue  #TODO: raise an exception 
            item = c.fetchone()

            if item[0]:
                rdata["date"] = item[0]           
            if item[2]:
                rdata["date_scraped"] = item[2]

            # put the key values in
            c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
            for key, value in c.fetchall():
                rdata[key] = value

            # over-ride any values with latlng (we could break it into two values) (may need to wrap in a try to protect)
            if item[1]:
                rdata["latlng"] = tuple(map(float, item[1].split(",")))
            else:
                rdata.pop("latlng", None)  # make sure this field is always a pair of floats

            allitems.append(rdata)

        c.close()
        return allitems

    # this accesses the tables defined in scraperlibs/scraperwiki/datastore/scheme.sql and accessed in datastore/save.py
    def data_dictlist(self, scraper_id, limit=1000, offset=0, start_date=None, end_date=None, latlng=None):   
        '''map from scraper_id and filters to dict representing row record for a particular scraper'''

        proxy   = self.dataproxy(scraper_id)
        rc, arg = proxy.data_dictlist(limit, offset, start_date, end_date, latlng)
        if not rc :
            raise Exception(arg)
        allitems = arg
        return allitems

    def data_summary(self, scraper_id=0, limit=1000, offset=0, start_date=None, end_date=None, latlng=None, column_order=None, private_columns=None):
        '''single table of all rows for a scraper'''
        try:
            allitems = self.data_dictlist(scraper_id, limit=limit, offset=offset, start_date=start_date, end_date=start_date, latlng=latlng)  
        except ValueError, e:
            allitems = [{"Unfortunate datastore error":str(e)}]
        return convert_dictlist_to_datalist(allitems, column_order, private_columns)


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
        sql = "SELECT COUNT(item_id) FROM items WHERE scraper_id='%s'" % guid
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        result = int(cursor.fetchone()[0])
        cursor.close()
        return result

    def has_geo(self, scraper_id):
        sql = "SELECT COUNT(item_id) FROM items WHERE scraper_id='%s' and latlng is not null and latlng <> ''" % scraper_id
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()[0] > 0
        cursor.close()
        return result

    def has_temporal(self, scraper_id):
        sql = "SELECT COUNT(item_id) FROM items WHERE scraper_id='%s' and date is not null" % scraper_id
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()[0] > 0
        cursor.close()
        return result

    def item_count_for_tag(self, guids):  # to delete
        guids = ",".join("'%s'" % guid for guid in guids)
        sql = "SELECT COUNT(*) FROM items WHERE scraper_id IN (%(guids)s)" % locals()
        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()[0]
        cursor.close()
        return result

    def recent_record_count(self, scraper_id, days):

        sql = "SELECT date(date_scraped) as date, count(date_scraped) as count FROM items "
        sql += "WHERE scraper_id='%s' and date_scraped BETWEEN DATE_SUB(CURDATE(), INTERVAL %d DAY) AND DATE_ADD(CURDATE(), INTERVAL 1 DAY)" % (scraper_id, days)
        sql += "GROUP BY date(date_scraped)"

        cursor = self.datastore_connection.cursor()
        cursor.execute(sql)
        date_counts = cursor.fetchall()

        #make a store, 
        return_dates = []
        all_dates = [datetime.datetime.now() + datetime.timedelta(i)  for i in range(-days, 1)]
        for all_date in  all_dates:
            #try and find an entry for this date in the query results
            count = 0
            for date_count in date_counts:        
                if str(date_count[0]) == all_date.strftime("%Y-%m-%d"):
                    count = date_count[1]

            #add the count to the return list
            return_dates.append(count)
        
        cursor.close()
        return return_dates

    #for example lists
    def example_scrapers(self, user, count):
        scrapers = []
        if user.is_authenticated():
            scrapers = user.code_set.filter(usercoderole__role='owner', wiki_type='scraper', deleted=False, published=True)[:count]
        else:
            scrapers = self.filter(deleted=False, featured=True).order_by('first_published_at')[:count]
        
        return scrapers
