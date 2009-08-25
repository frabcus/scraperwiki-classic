from detectors.scraperutils import ScrapeCachedURL
import urlparse
from BeautifulSoup import BeautifulSoup
import re
import sys

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
for monthtitle, monthurl in GetMonthArchivePages():
    GetPagesForMonth(monthtitle, monthurl)
    


