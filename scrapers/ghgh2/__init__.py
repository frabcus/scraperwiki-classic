from scraperutils import ScrapeCachedURL
import urlparse
from BeautifulSoup import BeautifulSoup
import re
import sys
import datetime
import codewiki.models as models


def ss(d):
    return re.sub("<", "&lt;", str(d))


def GetMonthArchivePages():
    res = [ ]
    urlfront = "http://www.london-fire.gov.uk/LatestIncidents.asp"
    text = ScrapeCachedURL(scraper_tag="londonfire_mainindex", name="frontpage", url=urlfront)
    soup = BeautifulSoup(text)
    rightcol = soup.find("div", { "class" : "col-right-int" })
    for option in rightcol.findAll("option"):
        monthtitle = "".join(option.contents).strip()
        monthurl = urlparse.urljoin(urlfront, option["value"])
        res.append((monthtitle, monthurl))
    return res
    
def GetPagesForMonth(monthtitle, monthurl):
    text = ScrapeCachedURL(scraper_tag="londonfire_monthindex", name=monthtitle, url=monthurl)
    soup = BeautifulSoup(text)    
    for h2 in soup.findAll("h2"):
        if h2.a:
            lurl = h2.a["href"]

            # their database gives 20 character hashcodes which they often (inconsistently) rewrite into something humanly readable
            cname = re.search("LastestIncidentsContainer_(.*?)\.asp", lurl).group(1)
            urlp = urlparse.urljoin(monthurl, lurl)
            print cname, urlp
            textp = ScrapeCachedURL(scraper_tag="londonfirepage", name=cname, url=urlp)
            
# main loop
def RunScrape():
    for monthtitle, monthurl in GetMonthArchivePages()[:2]:
        GetPagesForMonth(monthtitle, monthurl)

        
        
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


def Observe(tailurl):
    allkeyvalues = [ ]
    for detection in models.Detection.objects.filter(status="parsed"):
        allkeyvalues.extend(eval(detection.result))
    print len(allkeyvalues)
    
    print "<h1>Fire Callouts</h1>"
    print "<table>"
    print "<tr><th>Date</th><th>Title</th><th>Number firefighters</th></tr>"
    for kv in allkeyvalues:
        print "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (kv.get("startdate"), kv.get("title"), kv.get("firefighters"))
    print "</table>"


