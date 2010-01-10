from osgb import eastnorth_to_osgb, osgb_to_lonlat
from geo_helper import turn_wgs84_into_osgb36


class geopoint:
    def __init__(self):
        self.coordinatesystem == "EMPTY"
    
    # for now converts everything into OSGB    
    def latlng(self):
        
        if self.coordinatesystem == "OSeastingnorthing":
            oscoord = eastnorth_to_osgb(self.easting, self.northing, 5)
            lng, lat = osgb_to_lonlat(oscoord)
        
        elif self.coordinatesystem == "OSGB":
            lng, lat = osgb_to_lonlat(self.oscoord)
        
        elif self.coordinatesystem == "OSGB36":
            lng, lat = self.longitude, self.latitude
        
        elif self.coordinatesystem == "WGS84":
            sheight = (self.altitude == None and 200 or self.altitude)
            lat, lng, height = turn_wgs84_into_osgb36(self.latitude, self.longitude, sheight)
        
        else:
            lng, lat = None, None

        return [lat, lng]
            

# the different type objects for quickest access
class OSeastingnorthing(geopoint):
    def __init__(self, easting, northing):
        self.coordinatesystem = "OSeastingnorthing"
        self.easting = easting
        self.northing = northing
        
class OSGB(geopoint):
    def __init__(self, oscoord):
        self.coordinatesystem = "OSGB"
        self.oscoord = oscoord

class OSGB36(geopoint):
    def __init__(self, latitude, longitude):
        self.coordinatesystem = "OSGB36"
        self.latitude = latitude
        self.longitude = longitude

class WGS84(geopoint):
    def __init__(self, latitude, longitude, altitude=None):
        self.coordinatesystem = "WGS84"
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        
