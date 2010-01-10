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

# this sets deleted_run_id to flag a record is deleted, rather than actually deleting it
bSaveAllDeletes = False


def insert(data):
    """
    Inserts a single row
    """
    scraper_id = os.environ['SCRAPER_GUID']
  
    conn = connection.Connection()
    c = conn.connect()
    
    # there's apparently a good reason for doing it this way, and not using auto-increment
    c.execute("UPDATE sequences SET id=LAST_INSERT_ID(id+1);")
    c.execute("SELECT LAST_INSERT_ID();")
    item_id = c.fetchone()[0]
 
    # for date scraped
    str_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    # the v is typed and could be, for example, padded with zeros if it is of int type
    for k,v in data.items():  
        c.execute("INSERT INTO kv (`item_id`,`key`,`value`) VALUES (%s, %s, %s);", (item_id, k, str(v)))
  
    # --  `run_id`          varchar(255)    NOT NULL,
    # --  `deleted_run_id`  varchar(255)    NULL,
    
    hlatlng = str(data.get('latlng'))
    hdate = str(data.get('date'))     # this should be converted into a date object which saves natively into the database
    c.execute("INSERT INTO `items` (`scraper_id`,`item_id`,`unique_hash`,`date`, `latlng`, `date_scraped`) \
               VALUES (%s, %s, %s, %s, %s, %s);", (scraper_id, item_id, "deletethisvalue", hdate, hlatlng, str_now))
  
    
    # printing to the console
    ldata = { }
    for k, v in data.items():  
        ldata[cgi.escape(k)] = cgi.escape(str(v))
    print '&lt;scraperwiki:message type="data">%s&lt;/scraperwiki:message>' % json.dumps(ldata)
  
    return item_id

    

def __retrieve_item(c, item_id):
    """
    Loads single row given the item_id
    """
    if not c.execute("SELECT scraper_id, date_scraped FROM items WHERE item_id=%s", (item_id,)):
        return None
    scraper_id, date_scraped = c.fetchone()
    
    rdata = { "date_scraped": date_scraped }  
  
    c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
    for key, value in c.fetchall():
        rdata[key] = value
      
    return rdata


def __build_matches(matchrecord, scraper_id="current"):
    if scraper_id == "current":
        scraper_id = os.environ['SCRAPER_GUID']
        
    qquery  = ["SELECT items.item_id AS item_id FROM items"]
    qlist   = [ ]
        
    i = 0
    for key, value in matchrecord.items():
        qquery.append("INNER JOIN")
        qquery.append("kv AS kv%d" % i)
        qquery.append("ON")
        qquery.append("kv%d.item_id=items.item_id" % i)
        qquery.append("AND")
        qquery.append("kv%d.key=%%s" % i)
        qlist.append(key)
        if value:
            qquery.append("AND")
            qquery.append("kv%d.value=%%s" % i)
            qlist.append(value)
        i += 1
            
    # add this when the scheme gets updated
    #qquery.append("WHERE")
    #qquery.append("deleted_run_id IS NULL")
    
    if scraper_id:
        qquery.append("WHERE")
        qquery.append("items.scraper_id=%s")
        qlist.append(scraper_id)


    qquery.append("ORDER BY item_id")
    return " ".join(qquery), tuple(qlist)


def retrieve(matchrecord, scraper_id="current"):
    """
    Retrieves all records owned by scraper (of current scraper if scraper_id) filtered by matchrecord
    """
    conn = connection.Connection()
    c = conn.connect()
    
    query, qlist = __build_matches(matchrecord, scraper_id)
    #print query, qlist
    c.execute(query, qlist)
        
    result = [ ]
    item_idlist = c.fetchall()
    for item_idl in item_idlist:
        rdata = __retrieve_item(c, item_idl[0])
        if rdata:
            result.append(rdata)
    return result
    
    
def __delete_item(c, item_id):
    """
    Deletes single row given the item_id
    """
    if bSaveAllDeletes:
        run_id = os.environ['RUN_GUID']
        c.execute("UPDATE items SET deleted_run_id=%s WHERE item_id=%s", (run_id, item_id,))

    else:
        c.execute("DELETE FROM items WHERE item_id=%s", (item_id,))
        c.execute("DELETE FROM kv WHERE item_id=%s", (item_id,))


def delete(matchrecord, scraper_id="current"):
    """
    Deletes all records owned by scraper (of current scraper if scraper_id) filtered by matchrecord
    """
    conn = connection.Connection()
    c = conn.connect()
    
    query, qlist = __build_matches(matchrecord, scraper_id)
    #print query, qlist
    c.execute(query, qlist)
    
    result = [ ]
    item_idlist = c.fetchall()
    for item_idl in item_idlist:
        print "deleting", item_idl
        rdata = __delete_item(c, item_idl[0])
    

def save(unique_keys, data, date=None, latlng=None):
    """
    Standard save function that over-writes a record that shares the same values for the unique_keys
    """
    
    
    if date:
        data["date"] = date
    if latlng:
        data["latlng"] = latlng

    
    # fill in unique keys
    matchrecord = { }
    for key in unique_keys:
        matchrecord[key] = str(data[key])
        
    # always insert when unique_keys are empty 
    if unique_keys:   
        delete(matchrecord)
    
    insert(data)
    

  

  