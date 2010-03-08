from osgb import eastnorth_to_osgb, osgb_to_lonlat, lonlat_to_eastnorth
from geo_helper import turn_osgb36_into_wgs84

import urllib
import re
import sys
sys.path.append('..')
import connection

try:
  import json
except:
  import simplejson as json


'''standardized to wgs84 (if possible)'''

def gb_postcode_to_latlng(postcode):
    '''Convert postcode to latlng using google api'''
    return GBPostcode(postcode).latlng

def os_easting_northing_to_latlng(easting, northing):
    '''Convert easting, northing to latlng assuming altitude 200m'''
    return OSeastingnorthing(easting, northing).latlng

def extract_gb_postcode(string):
    postcode = False
    matches = re.findall(r'[A-Z][A-Z]?[0-9][A-Z0-9]? ?[0-9][ABDEFGHJLNPQRSTUWXYZ]{2}\b', string, re.IGNORECASE)

    if len(matches) > 0:
        postcode = matches[0]

    return postcode

""" Represents a lat/lng (wgs32 projection) """
class Point:
    def __init__(self, lat, lng):
        self.latlng = (lat = 0, lng = 0)

# implement above user functions through classes with their conversion outputs
class GBPostcode:   # (geopoint)
    
    def __init__(self, postcode):
        self.coordinatesystem = "GBPostcode"
        self.postcode = postcode
        self.latlng = None
        try:

            #open connection
            conn = connection.Connection()
            c = conn.cursor()
            sql = " select AsText(location) from postcode_lookup where postcode = %s"
            c.execute(sql, (postcode,))            
            result = c.fetchone()[0]
            if result:
                self.latlng = result.replace('POINT(', '').replace(')', '').split(' ')
                self.latlng = [float(self.latlng[0]), float(self.latlng[1])]
        except:
            self.latlng = None
            
    def __str__(self):
        return "GBPostcode('%s')" % self.postcode
    

class OSeastingnorthing:
    def __init__(self, easting, northing):
        self.coordinatesystem = "OSeastingnorthing"
        self.easting = easting
        self.northing = northing
            
        oscoord = eastnorth_to_osgb(self.easting, self.northing, 5)
        
        gb36lng, gb36lat = osgb_to_lonlat(oscoord)
            
        gb36height = 0  # guessed altitude of the point
        lat, lng, height = turn_osgb36_into_wgs84(gb36lat, gb36lng, gb36height)

        self.latlng = (lat, lng)
        

        
