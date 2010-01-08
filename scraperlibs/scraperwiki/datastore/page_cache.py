# encoding: utf-8
import hashlib
import os
import datetime
import connection

# this file is actually imported into scraperlibs.page_cache from the datastore directory

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


# test harness code to be run in a scraper
"""
from scraperwiki.datastore import *

text1 = "ggy" * 100
text2 = "&^%$__--=  " * 200
text3 = "33333" * 20
tag1 = "tag1"
tag2 = "tag2"
name1 = "name1"
name2 = "name2"
name3 = "name3"

# clear the database of pages
deletepagesbytag("")
assert len(getnamesfromtag("")) == 0

# set up three pages
savepage(tag1, name1, text1)
savepage(tag1, name2, text2)
savepage(tag2, name3, text3)

# positive function calls
assert len(getnamesfromtag("")) == 3
assert len(getnamesfromtag(tag1)) == 2
assert getnamesfromtag(tag2) == [name3]
deletepagebyname(name1)
assert getnamesfromtag(tag1) == [name2]
assert gettagbyname(name3) == tag2
deletepagesbytag(tag2)
assert getnamesfromtag("") == [name2]
assert getpagebyname(name2) == text2

# negative function calls
assert not getnamesfromtag(tag2)
assert not gettagbyname(name1)
assert not getpagebyname(name1)

# clear the three entries again
deletepagebyname(name2)
assert not getnamesfromtag("")
print "Done"
"""