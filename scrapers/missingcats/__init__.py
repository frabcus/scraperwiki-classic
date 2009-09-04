from scraperutils import ScrapeCachedURL

def Scrape():
    urlindex = "http://www.nationalpetregister.org/mp-cats.php?showold=yes"
    scrapertag_index = "missingcats_index"
    for i in range(40, 45):  # edit this to get different page ranges
        url = urlindex + "&page=" + str(i)
        text = ScrapeCachedURL(scraper_tag=scrapertag_index, name="page " + str(i), url=url)
        print i, len(text)

from BeautifulSoup import BeautifulSoup

import sys, re
import urllib, urlparse
import datetime


#CreateScopeUser(user_name, user_password, user_email) # run once    

def ss(d):
    return re.sub("<", "&lt;", str(d))

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def DoesApply(reading):
    return reading.scraper_tag == "missingcats_index" or reading.name[:4] == "page"
    

def ParseCattable(url, tt):
    col = tt.tr.findAll("td")
    
    res = {}
    i = 0
    if col[0].img:
        res["id"] = 0
    else:
        res["id"] = int(col[0].string)
        i += 1
    if col[i].img["alt"] == "Lost Pet Listed by RSPCA":
        i += 1
    res["photo"] = col[i].img["src"]
    res["title"] = col[i].img["alt"]
    i = i + 1
    res["description"] = col[i].contents[0].string
    if len(col[i].contents) > 2:
        res["type"] = col[i].contents[2].string
    i = i + 1
    res["animal_type"] = col[i].string
    i = i + 1
    res["county"] = col[i].string
    i = i + 1
    if col[i].a:
        i += 1
    mdate = re.match("(\w+) (\d+), (\d+)$", col[i].string)
    month, day, year = mdate.groups()
    imonth = months.index(month) + 1
    res["date"] = "%s-%02d-%02d" % (year, imonth, int(day))
    i = i + 1
    res["url"] = urlparse.urljoin(url, col[i].a["href"])
    
    return res
        

def Parse(reading):
    alldata = [ ]
    soup = BeautifulSoup(reading.contents())
    for tt in soup.findAll("table", ""):
        res = ParseCattable(reading.url, tt)
        res["reading"] = reading
        alldata.append(res)          
    return alldata



def Observe(tailurl):
    print "blank page"
