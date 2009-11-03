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
import datastore


unique_keys = ['message_id',]

data = {

'message_id' : '1',

'message' : 'This is an example',

'sender' : 'Sym',

}

datastore.save(unique_keys, data, latlng=[52.38431,1.11112])

"""
  return locals()