#  encoding: utf-8
#
import  datastore

#  Fetch from the data store for the current scraper. The argument
#  must be a dictionary of key-value pairs corresponding to the unique
#  key values when the data was saved
#
#       date            : Date stored against the data item
#       latlng          : Lat/long stored against the data item
#       date_scraped    : Date when the record was scraped
#       data            : Dictionary of all key-value pairs
#
def fetch (unique_keys) :

    ds = datastore.DataStore(None)
    rc, arg = ds.fetch (unique_keys)
    if not rc :
        raise Exception (arg) 

    return arg
