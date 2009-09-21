#!/usr/bin/python

import sys
import os
import urllib
import re
import MySQLdb
import datetime

now = datetime.datetime.now()
db = MySQLdb.connect(user="freesteel", passwd="meti998", db="metroscope")

def GetCursorDB():
    return db.cursor()

def dbescape(str):
    str = str.encode("string_escape", 'replace')
    return db.escape_string(str)

def ConstituencyPos(str, c):
    dstr = dbescape(str)
    if c:
        c.execute("SELECT lat, lon FROM metro_constituency_cache WHERE constituency='%s'" % dstr)
        a = c.fetchone()
        if a:
            return a[0], a[1]
    
    p = { "output":"xml", "name":str }
    fin = urllib.urlopen("http://www.theyworkforyou.com/api/getGeometry", urllib.urlencode(p))
    a = fin.read()
    fin.close()
    mlat = re.search("<centre_lat>([\-\d\.]*)</centre_lat>", a)
    mlon = re.search("<centre_lon>([\-\d\.]*)</centre_lon>", a)
    if not (mlat and mlon):
        print "Unrecognized constituency: :%s:" % str
        return None, None
    lat = float(mlat.group(1))
    lon = float(mlon.group(1))
    if c:
        c.execute("INSERT INTO metro_constituency_cache (constituency, lat, lon) VALUES ('%s', %f, %f)" % (dstr, lat, lon))
    return lat, lon


#http://services.mysociety.org/latlon-lookup-xml.php?input_postcode=cb11la
#
# <MYSOCIETY>
# <WGS84_LON>0.12829938932</WGS84_LON>
# <NORTHING>258697</NORTHING>
# <WGS84_LAT>52.2072862485</WGS84_LAT>
# <EASTING>545526</EASTING>
# <COORDSYST>G</COORDSYST>
# </MYSOCIETY>
#


def PostcodePos(postcode, c):
    if c:
        c.execute("SELECT lat, lon FROM metro_postcode_cache WHERE postcode='%s'" % postcode)
        a = c.fetchone()
        if a:
            return a[0], a[1]

    fin = urllib.urlopen("http://services.mysociety.org/latlon-lookup-xml.php?input_postcode=%s" % postcode)
    a = fin.read()
    fin.close()
    slon = re.search("<WGS84_LON>([\-\d\.]+)</WGS84_LON>", a)
    slat = re.search("<WGS84_LAT>([\-\d\.]+)</WGS84_LAT>", a)
    if not slon or not slat:
        return 0.0, 0.0
    lat = float(slat.group(1))
    lon = float(slon.group(1))
    if c:
        c.execute("INSERT INTO metro_postcode_cache (postcode, lat, lon) VALUES ('%s', %f, %f)" % (postcode, lat, lon))
    return lat, lon

if __name__ == "__main__":
    postcode = "l17ay"
    print "Content-type: text/html\n";
    lat, lon = PostcodePos(postcode, None)
    print "<h1>%s has lat %f, lon %f</h1>" % (postcode, lat, lon)
    print ConstituencyPos("Liverpool, Riverside")

