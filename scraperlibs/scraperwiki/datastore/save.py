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
    scraper_id = os.environ['SCRAPER_GUID']  # if scraper_id == '' then it's using an unsaved scraper, no GUID is allocated and should not interact with the database

    if scraper_id:
        conn = connection.Connection()
        c = conn.connect()
    
    if scraper_id:
        # there's apparently a good reason for doing it this way, and not using auto-increment on item_id, but it's not declared
        # (*probably* it's to enable the datastore to be distributed across several tables)
        c.execute("UPDATE sequences SET id=LAST_INSERT_ID(id+1);")
        c.execute("SELECT LAST_INSERT_ID();")
        item_id = c.fetchone()[0]
    else:
        item_id = 0
 
    # for date scraped
    str_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hlatlng = ""  # default blank value
        
    
    # the v is typed and could be, for example, padded with zeros if it is of int type
    for k, v in data.items():  
        sv = (v != None and str(v) or "")  # make None go to ""
        if scraper_id:
            c.execute("INSERT INTO kv (`item_id`,`key`,`value`) VALUES (%s, %s, %s);", (item_id, k, sv))
        
        # here we could detect if it is a latlng object and upgrade it to the latlng key
        #if sv[:7] == "OSGB36(":
        #    hlatlng = v
  
    # --  `run_id`          varchar(255)    NOT NULL,
    # --  `deleted_run_id`  varchar(255)    NULL,
    
    # get the special date value as long as it's of the right type
    hdate = data.get('date')
    if hdate != None and (type(hdate) != datetime.datetime and type(hdate) != datetime.date):
        print "Warning: date should be python.datetime", hdate, "is", type(hdate)
        hdate = None
    
    if 'latlng' in data:
         hlatlng = "%f,%f" % tuple(data["latlng"])  # this will throw exception if not exactly right
         data["latlng"] = hlatlng  # put the value back in so it's the same
         
            
    # should we put an try catch around here?
    if scraper_id:
        c.execute("INSERT INTO `items` (`item_id`, `unique_hash`, `scraper_id`,`date`, `latlng`, `date_scraped`) \
                   VALUES (%s, %s, %s, %s, %s, %s);", (item_id, "deletethisvalue", scraper_id, hdate, hlatlng, str_now))
          
    # printing to the console
    ldata = { }
    for k, v in data.items():  
        ldata[cgi.escape(k)] = cgi.escape(str(v))
    
    # this should print < but it crashes the javascript
    print '<scraperwiki:message type="data">%s' % json.dumps(ldata)   # don't put in the </scraperwiki:message> because it doesn't work like that!
     
    return item_id

    

def __retrieve_item(c, item_id):
    """
    Loads single row given the item_id
    """
    if not c.execute("SELECT scraper_id, date_scraped, latlng FROM items WHERE item_id=%s", (item_id,)):
        return None
    scraper_id, date_scraped, latlng = c.fetchone()
    
    rdata = { "date_scraped": date_scraped }  
  
    c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
    for key, value in c.fetchall():
        rdata[key] = value
      
    # over-write from our indexed valyue of latlng
    if latlng:
        rdata["latlng"] = latlng
        
    return rdata


def __build_matches(matchrecord, scraper_id):
    
    # scraper_id can be None to allow matching across whole database
    
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
    if scraper_id == "current":
        scraper_id = os.environ['SCRAPER_GUID']  
    if not scraper_id:
        print "Warning: cannot retrieve on unsaved scraper"
        return [ ]
    
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


def delete(matchrecord):
    """
    Deletes all records owned by scraper (of current scraper if scraper_id) filtered by matchrecord
    """
    scraper_id = os.environ['SCRAPER_GUID']  
    if not scraper_id:
        print "Warning: cannot delete on unsaved scraper"
        return 
    
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
    


def save(unique_keys, data, date=None, latlng=None):   # **kwargs
    # data.update(kwargs)   # merges two dicts to implement the October discussion on googlewave (not convinced it's a handy interface)
    
    """
    Standard save function that UPserts (over-writes) a record that shares the same values for the unique_keys
    """
    scraper_id = os.environ['SCRAPER_GUID']  # if scraper_id == '' then it's using an unsaved scraper, no GUID is allocated and should not interact with the database

    if date:
        data["date"] = date
    if latlng:
        data["latlng"] = latlng
    
    # fill in unique keys
    matchrecord = { }
    for key in unique_keys:
        matchrecord[key] = str(data[key])
        
    # always insert when unique_keys are empty 
    if scraper_id and unique_keys:   
        delete(matchrecord)
    
    insert(data)
    

  
