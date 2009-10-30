"""
This file defines scraper templates.

At the moment there is only a 'default' scraper that is loaded when 
creating a new scraper.  

In future we could make a few different template scrapers that can outline basic
tasks, like scraping a table, or a standard list/detial view.

TODO: write a working scraper here
"""

def default():
  title = "Untitled Scraper"
  description = None
  code = """
print "foo"
"""
  return locals()