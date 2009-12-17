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


# the records are in table items, which are joined on item_id to keyvalue pairs of table kv
# the current retrieval of from these tables is in web/scraper/managers/scraper.py
# perhaps the functions there should call this common module to keep it in one place
# -- or we could make a 3rd interface through dedicated webserver call that could be located on a different machine

# bug to fix: doesn't work work correctly for unique_keys=[] by forcing a save.  
# the uniquehash theory may be flawed because there is no requirement that the same set of unique_keys will always be used!
# may need a more basic filterdata value as used in __load_item
# we should get rid of kwargs = date=None, latlng=[None, None] as it is not useful
def save(unique_keys, data, **kwargs):
  """
  Save function
  """
  
  # convention: always add when unique_keys are empty
  if not unique_keys:
    unique_keys = data.keys()
    
  if isinstance(data,list):
    if kwargs:
      raise TypeError("""
        \tIncorrect use of arguments when saving multipul rows.  
        \tLook up 'saving multipul rows' in the suport pages for more information.
        """)
    ids = []
    for row in data:
      ids.append(__save_row(unique_keys, row))
    return ids
  else:
    # Add all the kwargs in to data for now
    data.update(kwargs)   # merges two dicts for now
    return __save_row(unique_keys, data)



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


def __save_row(unique_keys, data):
  """
  Takes a single row and saves it.
  """
  DUMMY_RUN = True
  if os.environ.has_key('SCRAPER_GUID'):
    scraper_id = os.environ['SCRAPER_GUID']
    DUMMY_RUN = False
  
  # Create a unique hash
  unique_hash = __create_unique(unique_keys, data)
  
  item = { 'unique_hash' : unique_hash }
  
  # copy over the primary items from the data or set their defaults
  for k in ['date', 'latlng']:  
    if k in data:
      item[k] = str(data[k])
      del data[k]
    else:
      item[k] = None
      
  
  new_item_id = None    
  if not DUMMY_RUN:
    conn = connection.Connection()
    c = conn.connect()
    
    # this won't work if the unique_keys list ever differs for the record
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
  
    # the v is typed and could be, for example, padded with zeros if it is of int type
    for k,v in data.items():  
      c.execute("INSERT INTO kv (`item_id`,`key`,`value`) VALUES (%s, %s, %s);", (item['item_id'], k, str(v)))
    
      # clean for printing to the console

  ldata = { }
  for k,v in data.items():  
    ldata[k] = cgi.escape(str(v))
  
  # output to the console
  print '<scraperwiki:message type="data">%s' % json.dumps(ldata)
  
  # maybe there's a more useful return value than this
  return new_item_id



def loadsingle(unique_keys, data):
  """
  UNDOCUMENTED: Loads a single row matching unique keys with same data
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
    
    if c.execute("SELECT item_id FROM items WHERE unique_hash=%s", (unique_hash,)):
      item_id = c.fetchone()[0]
      return __load_item(c, item_id, None)
    
  return None
    
    
def loadallofcurrentscraper(filterdata=None):
    """
    UNDOCUMENTED: Loads all rows produced by scraper of current GUID, filters by matching data
    """
    conn = connection.Connection()
    c = conn.connect()
    
    scraper_id = os.environ['SCRAPER_GUID']
    c.execute("SELECT item_id FROM items WHERE scraper_id=%s ORDER BY date, item_id", (scraper_id,))
    
    res = [ ]
    item_idlist = c.fetchall()
    for item_idl in item_idlist:
        rdata = __load_item(c, item_idl[0], filterdata)
        if rdata:
            res.append(rdata)
    return res
    

def deleteallofcurrentscraper(filterdata=None):
    """
    UNDOCUMENTED: Deletes all rows produced by scraper of current GUID, filters by matching data
    """
    conn = connection.Connection()
    c = conn.connect()
    
    scraper_id = os.environ['SCRAPER_GUID']
    c.execute("SELECT item_id FROM items WHERE scraper_id=%s ORDER BY date, item_id", (scraper_id,))
    
    res = [ ]
    item_idlist = c.fetchall()
    for item_idl in item_idlist:
        item_id = item_idl[0]
        rdata = __load_item(c, item_id, filterdata)
        if rdata:
            c.execute("DELETE FROM kv WHERE item_id=%s", (item_id,))
            c.execute("DELETE FROM items WHERE item_id=%s", (item_id,))
            res.append(rdata)
    return res

    
def loadallwithmatchingdata(filterdata):
    """
    UNDOCUMENTED: Loads everything out of the database that has matching filterdata.  
    would like to limit by scraper, but no way to uncover the SCRAPER_GUID from the useable scraper short_name
    """
    conn = connection.Connection()
    c = conn.connect()
    
    # find the longest key and use that to initially filter the results
    keyvs = [ (len(str(key)) + (value and len(str(value)) or 0), key, value)  for key, value in filterdata.items() ]
    keyvs.sort()
    assert len(keyvs) >= 1
    
    itemspartmatch = set()
    
    longestkey, longestvalue = keyvs[-1][1], keyvs[-1][2]
    if longestvalue:
        c.execute("SELECT item_id FROM kv WHERE `key`=%s AND `value`=%s GROUP BY item_id", (longestkey, longestvalue))
    else:
        c.execute("SELECT item_id FROM kv WHERE `key`=%s GROUP BY item_id", (longestkey,))
    for item_idl in c.fetchall():
        itemspartmatch.add(item_idl[0])
        
    for item_idl in c.fetchall():
        itemspartmatch.add(item_idl[0])
    
    res = [ ]
    item_idlist = c.fetchall()
    for item_id in itemspartmatch:
        rdata = __load_item(c, item_id, filterdata)
        if rdata:
            res.append(rdata)
    return res

    
def __load_item(c, item_id, filterdata):
    """
    Loads single row given the item_id, and returns None if it doesn't match the filterdata values (where value=None means we only match existence of key)
    """
    if not c.execute("SELECT scraper_id, date, latlng, date_scraped FROM items WHERE item_id=%s", (item_id,)):
        return None
    lscraper_id, date, latlng, date_scraped = c.fetchone()
    
    
    rdata = { "date_scraped": date_scraped }  
    if date:
        rdata["date"] = date
    if latlng:
        rdata["latlng"] = latlng
  
    # why do these particular columns need to be in silly quotes to stop a syntax error?  doesn't happen with items table
    c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
    
    # discard any rows that don't match the filterdata values
    for key, value in c.fetchall():
        fvalue = filterdata and filterdata.get(key)
        if fvalue != None and str(fvalue) != value:
            return None
        rdata[key] = value
      
    # bail out if there is a key missing
    if filterdata:
        for key in filterdata:
            if key not in rdata:
                return None
        
    return rdata
  

  
# test harness
if __name__ == "__main__":
  
  # Test one: Save a single row with a data dict passed
  unique_keys = ['message_id',]
  data = {
  'message_id' : '1',
  'message' : 'This is an example',
  'sender' : 'Sym',
  }
  save(unique_keys, data, date='2009-10-16', latlng=(52.38431,1.11112))

  
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
  
  
  