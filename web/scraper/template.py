"""
This file defines scraper templates.

At the moment there is only a 'default' scraper that is loaded when 
creating a new scraper.  

In future we could make a few different template scrapers that can outline basic
tasks, like scraping a table, or a standard list/detial view.

TODO: write a working scraper here
  (Users are more likely going to pull in code from a working scraper closest to their intended job, so 
  there's going to be a category of simple scrapers which people browse, and then duplicate from that)
"""

def default():
  title = "Untitled Scraper"
  description = None
  code = """
import scraperwiki
import BeautifulSoup

from scraperwiki import datastore

# Hello World Example #

#scrape page
html = scraperwiki.scrape('http://scraperwiki.com/hello_world.html')
page = BeautifulSoup.BeautifulSoup(html)

#find rows
for table in page.findAll('table'):
    for row in table.findAll('tr')[1:]: 

        #save to datastore
        data = {'message' : row.td.string,}
        datastore.save(unique_keys=['message'], data=data)


"""
  return locals()