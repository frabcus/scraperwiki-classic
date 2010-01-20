# encoding: utf-8
import hashlib
import os
import datetime
import connection

# this file is actually imported into scraperlibs.page_cache from the datastore directory

# it was put here (for now) because it accesses the same database as the datastore (though a different table)

def deletepagebyname(name):
    """Delete page function"""
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    return c.execute("DELETE FROM pages WHERE scraper_id=%s AND name=%s", (scraper_id, name))
    

def savepage(tag, name, text):
    """Save page function"""
    deletepagebyname(name)
    
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    
    now = datetime.datetime.now()
    str_now = now.strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO `pages` (`scraper_id`,`date_saved`,`tag`,`name`, `text`) \
               VALUES (%s, %s, %s, %s, %s);", (scraper_id, str_now, tag, name, text))

def deletepagesbytag(tag):
    """Deletes all pages matching tag"""
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    
    if tag:
        c.execute("DELETE FROM pages WHERE scraper_id=%s AND tag=%s", (scraper_id, tag)) 
    else:
        c.execute("DELETE FROM pages WHERE scraper_id=%s", (scraper_id,)) 

def getpagebyname(name):
    """Get page from cache"""
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    if c.execute("SELECT text FROM pages WHERE scraper_id=%s AND name=%s", (scraper_id, name)):  
        return c.fetchone()[0]
    return None

def gettagbyname(name):
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    if c.execute("SELECT tag FROM pages WHERE scraper_id=%s AND name=%s", (scraper_id, name)):  
        return c.fetchone()[0]
    return None

def getnamesfromtag(tag):
    """Get page from cache"""
    scraper_id = os.environ['SCRAPER_GUID']
    conn = connection.Connection()
    c = conn.connect()
    
    if tag:
        c.execute("SELECT name FROM pages WHERE scraper_id=%s AND tag=%s", (scraper_id, tag)) 
    else:
        c.execute("SELECT name FROM pages WHERE scraper_id=%s", (scraper_id,)) 
    
    return [ f[0]  for f in c.fetchall() ]

