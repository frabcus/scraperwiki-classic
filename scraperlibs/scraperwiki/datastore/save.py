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
import re
import  DataStore

# this sets deleted_run_id to flag a record is deleted, rather than actually deleting it
bSaveAllDeletes = False

# Global connection object
#conn = connection.Connection()

def insert(data):
    """
    Inserts a single row
    """
    scraper_id = os.environ['SCRAPER_GUID']   # if scraper_id == '' then it's using an unsaved scraper, no GUID is 

    if scraper_id:
        c = conn.cursor()

    if scraper_id:
        # there's a reason for doing it this way (not using auto-increment on item_id) 
        # probably to enable the datastore to be distributed across several tables
        c.execute("UPDATE sequences SET id=LAST_INSERT_ID(id+1);")
        c.execute("SELECT LAST_INSERT_ID();")
        item_id = c.fetchone()[0]
    else:
        item_id = 0
 
    # extract the values on the special fields (we don't pop them, so their values get saved into the database as normal values)
    hlatlng = data.get("latlng", "")  
    hdate = data.get('date', None)
    hdate_scraped = data.get('date_scraped', None)

    # insert the key-values
    for k, v in data.items():  
        # the v is typed and could be, for example, padded with zeros if it is an int type
        sv = (v != None and v or "")  # convert None to ""
        #if sv[:7] == "OSGB36(":   hlatlng = v  # find latlng keys that aren't called latlng

        if scraper_id:
            c.execute("INSERT INTO kv (`item_id`,`key`,`value`) VALUES (%s, %s, %s);", (item_id, k, sv))
  
    
    # verify and correct the three special values
    if hdate != None and (type(hdate) != datetime.datetime and type(hdate) != datetime.date):
        print "Warning: date should be a python.datetime", hdate, "is", type(hdate)
        hdate = None
    
    if hdate_scraped != None and type(hdate_scraped) != datetime.datetime:
        print "Warning: date_scraped should be a python.datetime", hdate_scraped, "is", type(hdate)
        hdate_scraped = None
    if hdate_scraped == None:
        hdate_scraped = datetime.datetime.now()
    
    # fully verify and format the latlng field
    if hlatlng != None and ((type(hlatlng) == list) or (type(hlatlng) == tuple)) and len(hlatlng) == 2 and \
       ((type(hlatlng[0]) == int) or (type(hlatlng[0]) == float)) and \
       ((type(hlatlng[1]) == int) or (type(hlatlng[1]) == float)):
         hlatlng = "%020f,%020f" % tuple(hlatlng)  # this will throw exception if not exactly right
    else:
        if hlatlng:
            print "Warning: latlng must be a tuple of values (float, float)"
        hlatlng = None
         
    
    # should we put an try catch around here?
    if scraper_id:
        c.execute("INSERT INTO `items` (`item_id`, `unique_hash`, `scraper_id`, `date`, `latlng`, `date_scraped`) \
                   VALUES (%s, %s, %s, %s, %s, %s);", (item_id, "deletethisvalue", scraper_id, hdate, hlatlng, hdate_scraped))
          
    # printing to the console
    ldata = { }
    for k, v in data.items():
        ldata[cgi.escape(k)] = cgi.escape(v)
    
    # this should print < but it crashes the javascript
    print '<scraperwiki:message type="data">%s' % json.dumps(ldata)   # don't put in the </scraperwiki:message> because it doesn't work like that!
     
    return item_id


def __retrieve_item(c, item_id):
    """
    Loads single row given the item_id
    """
    if not c.execute("SELECT scraper_id, date, date_scraped, latlng FROM items WHERE item_id=%s", (item_id,)):
        return None
    scraper_id, date, date_scraped, latlng = c.fetchone()
    
    rdata = { "date_scraped": date_scraped }  # the only value which gets created on save
    c.execute("SELECT `key`, `value` FROM kv WHERE item_id=%s", (item_id,))
    for key, value in c.fetchall():
        rdata[key] = value
      
    # over-write from our indexed values (which will be the same, but with the proper type)
    if latlng:  
        rdata["latlng"] = tuple(map(float, latlng.split(",")))
    if date:  
        rdata["date"] = date
        
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
    
    c = conn.cursor()
    
    query, qlist = __build_matches(matchrecord, scraper_id)
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
    if bSaveAllDeletes:  # not fully implemented
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

    c = conn.cursor()
    
    query, qlist = __build_matches(matchrecord, scraper_id)
    c.execute(query, qlist)
    
    result = [ ]
    item_idlist = c.fetchall()
    for item_idl in item_idlist:
        #print "deleting", item_idl
        __delete_item(c, item_idl[0])
        result.append(item_idl[0])
    return result


def save (unique_keys, data, date = None, latlng = None) :

    ds = DataStore.DataStore()
    rc, arg = ds.save (unique_keys, data, date, latlng)
    if not rc :
        raise Exception (arg) 

    pdata = {}
    for key, value in data.items():
        pdata[cgi.escape(key)] = cgi.escape(str(value))
    
    print '<scraperwiki:message type="data">%s' % json.dumps(pdata)
    return arg

def saveX(unique_keys, data, date=None, latlng=None):
    """
    Standard save function that UPserts (over-writes) a record that shares the same values for the unique_keys
    as long as it is new (does not overwrite same record, so leaves date_scraped the same 
    and returns the list of records that were over-written (deleted) so you can tell if you have put in new records
    """
    scraper_id = os.environ['SCRAPER_GUID']  # if scraper_id == '' then it's using an unsaved scraper, no GUID is allocated and should not interact with the database

    # now convert the data into strings (so it is at least consistent with what comes back from the database)
    sdata = { }
    matchrecord = { }
    for k, v in data.items():
        sk = re.sub("\s", "_", k)  # convert spaces to underscores (found in insert function, not sure why we need it, but needs to be done at this level if anywhere)
        if v:
            if k in ["date", "latlng", "date_scraped" ]:
                sv = v  # leave these objects intact
            else:
                # sv = str(v)
                # Don't cast to string
                sv = v
        else:
            sv = ""
        
        sdata[sk] = sv
        
        if k in unique_keys:
            matchrecord[sk] = sv
    
    # merge special values into the main data
    if date:
        sdata["date"] = date
    if latlng:
        sdata["latlng"] = latlng
    
            
    item_idlist = [ ]
    if scraper_id:
        c = conn.cursor()
        
        # fetch items that match for the unique_keys
        if unique_keys:  # (always insert if no unique_keys)
            query, qlist = __build_matches(matchrecord, scraper_id)
            c.execute(query, qlist)
            result = [ ]
            item_idlist = c.fetchall()
        
    # case of exactly one item.  If it matches our data exactly, then quit
    if scraper_id and len(item_idlist): 
         rdata = __retrieve_item(c, item_idlist[0][0])  # it's a list if singlet lists
         
         # make the data comparable
         if "date_scraped" not in data:
             del rdata["date_scraped"]  
             
         if rdata == sdata:
             return "record exists"
    
    nrecordsoverwritten = len(item_idlist)
    if scraper_id:
        for item_idl in item_idlist:
            __delete_item(c, item_idl[0])
    
    insert(sdata)
    
    if nrecordsoverwritten:
        return "record inserted"
    elif nrecordsoverwritten == 1:
        return "record updated"
    return "%d records deleted, 1 inserted" % nrecordsoverwritten

  
