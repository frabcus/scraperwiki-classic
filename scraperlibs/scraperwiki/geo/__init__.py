from osgb import eastnorth_to_osgb, osgb_to_lonlat, lonlat_to_eastnorth
from geo_helper import turn_osgb36_into_wgs84, turn_eastingnorthing_into_osgb36, turn_eastingnorthing_into_osie36, turn_osie36_into_wgs84

import urllib2
import re
import sys
sys.path.append('..')
from scraperwiki.datastore import connection
from scraperwiki.datastore import DataStore

try:
  import json
except:
  import simplejson as json


'''standardized to wgs84 (if possible)'''

def gb_postcode_to_latlng(postcode):

    if not postcode :
        return None
    ds = DataStore (None)
    rc, arg = ds.postcodeToLatLng (postcode)
    if not rc :
        raise Exception (arg)
    return arg

#    '''Convert postcode to latlng maxmander's code. (in future use a scraperwiki-rpc)'''
#    if not postcode:
#        return None
#    purl = "http://maxmanders.co.uk/ukgeocode/postcode/" + urllib2.quote(postcode)
#    res = urllib2.urlopen(purl).read()
#    latlng = map(float, re.findall("(?:<lat>|<lon>)(.*?)</", res))
#    if not latlng:
#        return None
#    return latlng

def os_easting_northing_to_latlng(easting, northing, grid='GB'):
    '''Convert easting, northing to latlng assuming altitude 200m'''
    if grid == 'GB':
        oscoord = turn_eastingnorthing_into_osgb36(easting, northing)
        latlng = turn_osgb36_into_wgs84(oscoord[0], oscoord[1], 200)
    elif grid == 'IE':
        oscoord = turn_eastingnorthing_into_osie36 (easting, northing)
        latlng = turn_osie36_into_wgs84(oscoord[0], oscoord[1], 200)
    return latlng[:2]

def extract_gb_postcode(string):
    postcode = False
    matches = re.findall(r'[A-Z][A-Z]?[0-9][A-Z0-9]? ?[0-9][ABDEFGHJLNPQRSTUWXYZ]{2}\b', string, re.IGNORECASE)

    if len(matches) > 0:
        postcode = matches[0]

    return postcode


