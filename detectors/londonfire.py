# New file#
from scraperutils import ScrapeURL, SaveScraping, FetchCorrectedText, ScrapeCachedURL, FetchNames
from BeautifulSoup import BeautifulSoup

import sys, re
import urllib, urlparse
import datetime

def ss(d):
    return re.sub("<", "&lt;", str(d))


months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def dateconvert(d):
    mdate = re.match("(\d+) (\w+) (\d+)$", d)
    day, month, year = mdate.groups()
    imonth = months.index(month) + 1
    return datetime.datetime(int(year), imonth, int(day)) 


def DoesApply(reading):
    return reading.scraper_tag == "londonfirepage"
    
def Parse(reading):
    alldata = [ ]
    soup = BeautifulSoup(reading.contents())
    dd = soup.find("div", { "class" : "col-center-int-wider" })
    res = { }
    res["title"] = str(dd.h1.contents[0]).strip()
    date = dateconvert(str(dd.h2.contents[0]).strip())
    res["date"] = str(date)
    paras = [ str(p.contents[0]).strip()  for p in dd.findAll("p") ]
    #res["url"] = reading.url
    text = " ".join(paras)
    mfirefighters = re.search("(\d+) firefighters", text)
    mcalledat = re.search("called at (\d\d)(\d\d)", text)
    mundercontrol = re.search("under control by (\d\d\d\d)", text)
    if mfirefighters:
        res["firefighters"] = int(mfirefighters.group(1))
    if mcalledat:
        starttime = datetime.datetime(date.year, date.month, date.day, int(mcalledat.group(1)), int(mcalledat.group(2)))
        res["startdate"] = str(starttime)
    if mundercontrol:
        res["undercontrolby"] = mundercontrol.group(1)
    alldata.append(res)
    return alldata


