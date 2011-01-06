# code ported from http://scraperwiki.com/views/python-api-access/

import urllib

try: import json
except: import simplejson as json

apiurl = "http://api.scraperwiki.com/api/1.0/"
#apiurl = "http://localhost:8010/api/1.0/"   # for local operation
apilimit = 500


def getKeys(name):
    query = {"name":name}
    url = "%sdatastore/getkeys?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def generateData(urlbase, limit, offset):
    count = 0
    loffset = 0
    while True:
        if limit == -1:
            llimit = apilimit
        else:
            llimit = min(apilimit, limit-count)
            
        url = "%s&limit=%s&offset=%d" % (urlbase, llimit, offset+loffset)
        ljson = urllib.urlopen(url).read()
        lresult = json.loads(ljson)
        for row in lresult:
            yield row

        count += len(lresult)
           
        if len(lresult) < llimit:  # run out of records
            break
            
        if limit != -1 and count >= limit:    # exceeded the limit
            break

        loffset += llimit

def getData(name, limit=-1, offset=0):
    urlbase = "%sdatastore/getdata?name=%s" % (apiurl, name)
    return generateData(urlbase, limit, offset)

def getDataByDate(name, start_date, end_date, limit=-1, offset=0):
    urlbase = "%sdatastore/getdatabydate?name=%s&start_date=%s&end_date=%s" % (apiurl, name, start_date, end_date)
    return generateData(urlbase, limit, offset)

def getDataByLocation(name, lat, lng, limit=-1, offset=0):
    urlbase = "%sdatastore/getdatabylocation?name=%s&lat=%f&lng=%f" % (apiurl, name, lat, lng)
    return generateData(urlbase, limit, offset)
    
def search(name, filterdict, limit=-1, offset=0):
    filter = "|".join(map(lambda x: "%s,%s" % (urllib.quote(x[0]), urllib.quote(x[1])), filterdict.items()))
    urlbase = "%sdatastore/search?name=%s&filter=%s" % (apiurl, name, filter)
    return generateData(urlbase, limit, offset)



def getInfo(name, version=None, history_start_date=None, quietfields=None):
    query = {"name":name}
    if version:
        query["version"] = version
    if history_start_date:
        query["history_start_date"] = history_start_date
    if quietfields:
        query["quietfields"] = quietfields
    url = "%sscraper/getinfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def getRunInfo(name, runid=None):
    query = {"name":name}
    if runid:
        query["runid"] = runid
    url = "%sscraper/getruninfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def getUserInfo(username):
    query = {"username":username}
    url = "%sscraper/getuserinfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def scraperSearch(lquery):
    query = {"query":lquery}
    url = "%sscraper/search?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)
