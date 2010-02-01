from osgb import eastnorth_to_osgb, osgb_to_lonlat
from geo_helper import turn_wgs84_into_osgb36

import urllib
import re

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


# implement above user functions through classes with their conversion outputs
class GBPostcode:   # (geopoint)
    def fetchfromgoogle(self):
        # key for http://127.0.0.1:8000/ version
        #apikey = "ABQIAAAAvB8NItiEo8pwItcndDdiQxTpH3CbXHjuCVmaTc5MkkU4wO1RRhSA_yE1yF9gii01shzxoGTMy56I6A"
        
        # key for http://alpha.scraperwiki.com version
        apikey = "ABQIAAAAvB8NItiEo8pwItcndDdiQxS-0rhzH36yeeaqLtvzOYff_BDsWxRd8-RHcLV2SLWVG5cUzghJCde61g"

        googlegeourl = "http://maps.google.com/maps/geo?q=%s&output=json&gl=uk&oe=utf8&sensor=true_or_false&key=%s" % (urllib.quote(self.postcode), apikey)
        self.response = json.loads(urllib.urlopen(googlegeourl).read())
    
    
    def __init__(self, postcode):
        self.coordinatesystem = "GBPostcode"
        self.postcode = postcode
        self.latlng = None
        try:
            self.fetchfromgoogle()
            coordinates = self.response['Placemark'][0]['Point']['coordinates']
            self.latlng = (coordinates[1], coordinates[0])
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
            
        gb36height = 200  # guessed altitude of the point
        lat, lng, height = turn_wgs84_into_osgb36(gb36lat, gb36lng, gb36height)

        self.latlng = (lat, lng)
        

        
