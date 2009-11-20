# encoding: utf-8
import hashlib
import os
import datetime
import connection
try:
  import json
except:
  import simplejson as json

import cgi

def save(unique_keys, data=None, **kwargs):
  """
  Save function
  """
  
  if not data:
    data = {}
  if isinstance(data,list):
    if kwargs:
      raise TypeError("""
        \tIncorrect use of arguments when saving multipul rows.  
        \tLook up 'saving multipul rows' in the suport pages for more information.
        """)
    ids = []
    for row in data:
      ids.append(__save_row(unique_keys,row))
    return ids
  else:
    return __save_row(unique_keys, data, kwargs)



# slight issue with this method in case unique_keys are ever a different subset
# we're almost getting the the realm where they should be part of their own table
# with the other key values hanging off them
def __create_unique(unique_keys, data):
  data_set = set(data)
  unique_keys = set(unique_keys)
  
  if not unique_keys.issubset(data_set):
      raise ValueError("""
        key(s) [%s] not in data.
        `unique_keys` must only contain keys that exist in `data`.
        See the support pages for more information
        """ % ','.join( ['"%s"' % k for k in unique_keys.difference(data)] ))

  unique_values = [str(data[v]) for v in unique_keys]
  return hashlib.md5("%s" % ("≈≈≈".join(unique_values))).hexdigest()

indexed_rows = ['date', 'latlng']  # global

def __save_row(unique_keys, data, kwargs):
  """
  Takes a single row and saves it.
  """
  DUMMY_RUN = True
  if os.environ.has_key('SCRAPER_GUID'):
    scraper_id = os.environ['SCRAPER_GUID']
    DUMMY_RUN = False
  
  # Add all the kwargs in to data
  data.update(kwargs)   # merges two dicts

  # Create a unique hash
  unique_hash = __create_unique(unique_keys, data)
  
  for k in indexed_rows:
    if k not in data.keys():
      data[k] = None
  item = {'unique_hash' : unique_hash}
  for k,v in data.items():
    if k in indexed_rows:
      item[k] = v
    if v is None:
      del data[k]
  
  
  new_item_id = None    
  if not DUMMY_RUN:
    conn = connection.Connection()
    c = conn.connect()
    
    if c.execute("SELECT item_id FROM items WHERE unique_hash=%s", (unique_hash,)):  
      item_id = c.fetchone()[0]
      c.execute("DELETE FROM kv WHERE item_id=%s", (item_id,))
      c.execute("DELETE FROM items WHERE unique_hash=%s", (unique_hash,))
  
    c.execute("UPDATE sequences SET id=LAST_INSERT_ID(id+1);")
    c.execute("SELECT LAST_INSERT_ID();")
    new_item_id = c.fetchone()[0]
    item['item_id'] = new_item_id
 
    
    # for date scraped
    now = datetime.datetime.now()
    str_now = now.strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO `items` (`scraper_id`,`item_id`,`unique_hash`,`date`, `latlng`, `date_scraped`) \
      VALUES (%s, %s, %s, %s, %s, %s);", (scraper_id, item['item_id'], unique_hash, item['date'], item['latlng'], str_now))
  
    for k,v in data.items():  
      c.execute("""INSERT INTO kv (`item_id`,`key`,`value`) VALUES (%s, %s, %s);""", (item['item_id'], k,v))
    
      # clean for printing to the console

  ldata = { }
  for k,v in data.items():  
    ldata[k] = cgi.escape(str(v))
  
  print '<scraperwiki:message type="data">%s' % json.dumps(ldata)
  return new_item_id



def load(unique_keys, data):
  """
  Load function
  """
  
  return __load_row(unique_keys, data)


def __load_row(unique_keys, data):
  """
  Loads a single row matching unique keys with same data
  """
  DUMMY_RUN = True
  if os.environ.has_key('SCRAPER_GUID'):
    scraper_id = os.environ['SCRAPER_GUID']
    DUMMY_RUN = False
  
  # Create a unique hash
  unique_hash = __create_unique(unique_keys, data)
  
  item = {'unique_hash' : unique_hash}
  
  new_item_id = None    
  if not DUMMY_RUN:
    conn = connection.Connection()
    c = conn.connect()
    
    if not c.execute("SELECT scraper_id, item_id, unique_hash, date, latlng, date_scraped FROM items WHERE unique_hash=%s", (unique_hash,)):
      return { }
    lscraper_id, item_id, lunique_hash, date, latlng, date_scraped = c.fetchone()
    
    # this allows us to fetch entries from other scrapers.  
    # we need some way to relate the SCRAPER_GUID to the scraper short_name
    # assert lscraper_id == scraper_id
    
    rdata = { "date_scraped": date_scraped }  
  
    # why do the columns need to be in quotes?
    c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
    for key, value in c.fetchall():
      rdata[key] = value
    
  return rdata
  
  
if __name__ == "__main__":
  
  # Test one: Save a single row with a data dict passed
  unique_keys = ['message_id',]
  data = {
  'message_id' : '1',
  'message' : 'This is an example',
  'sender' : 'Sym',
  }
  save(unique_keys, data, date='16/10/2009', latlng=[52.38431,1.11112])

  
  # test two: Save a single row without a data dict, just named arguments
  print save(['id'], id=3, name='Sym', something_else='foo')
  
  # test three: Save many rows
  unique_keys = ['message_id']
  data = [
  {
  'message_id' : '1',
  'message' : 'This is an example',
  'sender' : 'Sym',
  },
  {
  'message_id' : '2',
  'message' : 'This is an example reply',
  'sender' : 'Someone Else',
  }
  ]
  print save(unique_keys, data)
  
  
  