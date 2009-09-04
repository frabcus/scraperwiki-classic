from scraperutils import SaveScraping, ListWikipediaDumps
import xml.dom.minidom
import datetime

# loads 

def LoadPage(page, wpdump):
    titlenode = page.getElementsByTagName("title")[0].firstChild
    timestamp = datetime.datetime.strptime(page.getElementsByTagName("timestamp")[0].firstChild.nodeValue, "%Y-%m-%dT%H:%M:%SZ")
    title = titlenode.nodeValue.strip()
    text = page.getElementsByTagName("text")[0].firstChild.nodeValue.encode("utf8")
    print title, len(text), timestamp
    SaveScraping(scraper_tag="wikipediadump", name=title, url="file://"+wpdump, text=text, timestamp=timestamp)

def Scrape():
    wpdumps = ListWikipediaDumps()
    for wpdump in wpdumps:
        fin = open(wpdump)
        wptext = fin.read()
        fin.close()
        pages = xml.dom.minidom.parseString(wptext).getElementsByTagName("page")
        for page in pages:
            LoadPage(page, wpdump)
    
