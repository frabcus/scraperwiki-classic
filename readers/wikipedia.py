from detectors.scraperutils import ScrapeURL, SaveScraping, FetchCorrectedText, FetchNames
from detectors.scraperutils import ListWikipediaDumps

wpdumps = ListWikipediaDumps()
for wpdump in wpdumps:
    fin = open(wpdump)
    text = fin.read().decode("latin1")
    fin.close()
    print "hi"
    SaveScraping(scraper_tag="wikipediadump", name=wpdump, url="file://"+wpdump, text=text)
    print wpdump, len(text)

    
    
