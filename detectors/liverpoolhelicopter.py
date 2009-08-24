#
from scraperutils import ScrapeURL, SaveScraping, FetchCorrectedText, FetchNames
from scraperutils import CreateScopeUser, PostData

import sys, re

scraper_tag = "liverpoolhelicopter"

user_name = "goatchurch"
user_password = "garfield"
user_email = "julian@goatchurch.org.uk"

import urllib
import re
import datetime
import sys

#CreateScopeUser(user_name, user_password, user_email) # run once

months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
def GetAllMonths():
    res = [ ]
    for m in range(1, 13):
        if m == 9:
            res.append(("2006-09", "sept06"))
        elif m >= 6:
            res.append(("2006-%02d" % m, months[m - 1] + "06"))

        res.append(("2007-%02d" % m, months[m - 1] + "07"))

        if m == 1:
            res.append(("2008-01", "jan08"))
        if m == 2:
            res.append(("2008-02", "feb08"))
        if 3 <= m <= 11:
            res.append(("2008-%02d" % m, months[m - 1] + "08"))                    
    res.sort()
    res = [("2009-01", "january09")]
    return res

if "scrape" in sys.argv:
    for mth, mthurl in GetAllMonths()[:]:
        url = "http://www.merseyside.police.uk/html/aboutus/departments/air-support/whereabouts/%s.htm" % mthurl
        text = ScrapeURL(url=url)
        SaveScraping(scraper_tag=scraper_tag, name=mth, url=url, text=text)

def ParseRow(row):
    cols = []
    for c in re.findall('(?s)<td[^>]*>(.*?)</td>', row):
        c = re.sub("<[^>]*>", " ", c)
        c = re.sub("\s\s+", " ", c)
        c = c.strip()
        cols.append(c)
    return cols

def PostPatrol(district, datetime, title, summary, url):
    data = {"user_name":user_name, "user_password":user_password}
    data["district"] = district
    data["summary"] = summary
    data["title"] = title
    data["evt_time"] = datetime
    data["url"] = url
    data["source"] = "liverpoolhelicopter"
    data["non_replace_field"] = "url, district, title"
    print data
    PostData(data)

def ParseMonth(text, monthurl):
    rows = re.findall('(?s)<tr valign="top" class="bodytext">(.*?)</tr>', text)
    for row in rows:
        date, time, district, title, summary = ParseRow(row)
        districts = [ d.strip()  for d in re.split("/", district) ]
        if re.match("&nbsp;", date) and re.match("&nbsp;", title):
            continue
        if re.match("&nbsp;", time):
            time = "12.00"
        mdate = re.match("(\d\d)[/.](\d\d)[/.](\d\d)", date)
        mtime = re.match("(\d\d)[\.:]?(\d\d)", time)
        #print date, time, district
        hour = int(mtime.group(1))
        day = int(mdate.group(1))
        if hour == 24:
            day += 1
            hour = 0
        dt = datetime.datetime(2000 + int(mdate.group(3)), int(mdate.group(2)), day, hour, int(mtime.group(2)))

        PostPatrol(district, dt, title, summary, monthurl)
        

# split districts at / and make a list of them, and how to get the lat lon from it.

if "parse" in sys.argv:
    mths = [ mth  for mth in FetchNames(scraper_tag)  if re.match("\d\d\d\d-\d\d", mth) ]
    print mths
    for mth in mths[-1:]:
        text, url = FetchCorrectedText(scraper_tag, mth)
        print "//localhost/metroscope/scraped/%s/%s" % (scraper_tag, mth)
        ParseMonth(text, url)


