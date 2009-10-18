#!/usr/bin/python

import sys
import os
import datetime
import re
import urllib, urlparse

thisurl = "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py"

def AddEntry(params):
    params["user_id"] = "danheeks"
    params["user_password"] = "hjk23498"
    params["submit"] = "post"
    fin = urllib.urlopen(thisurl, urllib.urlencode(params))
    res = fin.read()
    fin.close()
    mres = re.search("<tr><td>messid</td><td>(\d+)( new)?</td></tr>", res)
    if mres:
        messid = int(mres.group(1))
        return messid, mres.group(2) and ":added:" or ":present:"
    print res
    return messid, "\n\n*** Failed ***\n"


def GetProjectsURLs():
    return "http://www.merseyside.police.uk/html/aboutus/departments/air-support/whereabouts/june08.htm"

def ParseProjectData(pagestring):
    # date, time, area, incident, outcome
    entries = re.findall('<tr valign="top" class="bodytext">([\s\S]*?)</tr>', pagestring)

    print len(pagestring)

    print 'number of entries = ', len(entries)

    data = []

    for entry in entries:
        entry_data = re.findall('<td[\s\S]*?>(?:<p[^>]*>)?(?:<div[^>]*>)?([\s\S]*?)(?:</p>)?</td>', entry)
        #strip <br>/n
        new_entry_data = []
        for item in entry_data:
            item = item.replace('<br>', '')
            item = item.replace('\n', '')
            item = item.replace('</p[^>]*>', '')
            item = item.replace('<p[^>]*>', '')
            new_entry_data.append(item)
        data.append(new_entry_data)

    return data

def GetLocationFromMultiMap(multimapurl):
    fin = urllib.urlopen(multimapurl)
    multimapxml = fin.read()
    fin.close()
    postcode = ''
    lat = 0
    lon = ''
    m_postcode = re.search('<PostalCode>([\s\S]*?)</PostalCode>', multimapxml)
    if m_postcode != None:
        postcode = m_postcode.group(1)
    m_lat = re.search('<Lat>([\s\S]*?)</Lat>', multimapxml)
    if m_lat != None:
        lat = m_lat.group(1)
    m_lon = re.search('<Lon>([\s\S]*?)</Lon>', multimapxml)
    if m_lon != None:
        lon = m_lon.group(1)
    return lat, lon, postcode

def UpdateMerseyHelicopter():
    urlps = GetProjectsURLs()
    fin = urllib.urlopen(urlps)
    hlpage = fin.read()
    fin.close()
    data = ParseProjectData(hlpage)

    for entry_data in data:
        date, time, area, incident, outcome = entry_data

        # get a longitude and latitude given from the location
        area.strip()
        encoded_area = urllib.urlencode({"qs":area, "countryCode":"gb"})
        multimapurl = "http://developer.multimap.com/API/geocode/1.2/OA08062116328674416?" + encoded_area
        lat, lon, postcode = GetLocationFromMultiMap(multimapurl)

        if lat == 0:
             print "0 latitude for " + area
#            multimapurl = "http://developer.multimap.com/API/geocode/1.2/OA08062116328674416?qs=" + area + ", Liverpool&countryCode=gb"
#            lat, lon, postcode = GetLocationFromMultiMap(multimapurl)
#            print "new latitude calculated with Liverpool added"
#            print lat, lon, postcode, multimapurl

        m_date = re.search('(\d\d)[/\.](\d\d)[/\.](\d\d)', date)
        day = m_date.group(1)
        month = m_date.group(2)
        year = "20" + m_date.group(3)

        m_time = re.search('(\d\d)(\d\d)hrs', time)
        hour = ''
        minutes = ''
        if m_time == None:
            m_time = re.search('(\d\d)[/\.](\d\d)', time)
            if m_time == None:
                m_time = re.search('(\d\d)(\d\d)', time)

        if m_time:
            hour = m_time.group(1)
            minutes = m_time.group(2)

        print m_time
        print hour, minutes

        if hour == '24':
            hour = '0'

        evt_time = datetime.datetime( int(year), int(month), int(day), int(hour), int(minutes) )       
        print evt_time.isoformat()

        messid, mess = AddEntry({"src":"merseyjune", "title":incident, "district":area, "postcode":postcode, "lat":lat, "lon":lon, "quantity":outcome, "non_replace_field":"evt_time title", "evt_time":evt_time.isoformat()})
        print messid, mess


if __name__ == "__main__":
    UpdateMerseyHelicopter()


