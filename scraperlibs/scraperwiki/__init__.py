__doc__ = """ScraperWiki Utils - to be replaced by proper urllib over-riding"""
__version__ = "ScraperWiki_0.0.1"

import urllib2, cookielib


# global object handles cookies which work within the same session for now
# this will be formalized and made explicit when we make the urllib wrapping cache system
# that archives all the cookies for re-running the scraper code against
cj = cookielib.CookieJar()
urllibopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


# over-ride the default value of [('User-agent', 'Mozilla/5.0')]
urllibopener.addheaders = [('User-agent', 'Scraperwiki/October Blue Fountain')]
    

# should the exceptions be caught here?  
# should the print statements  go to different streams?
def ScrapeURL(url, params=None):
    '''get html text given url and parameter map'''
    data = params and urllib.urlencode(params) or None
    try:
        fin = urllibopener.open(url, data)
        text = unicode(fin.read(), errors="replace").encode("ascii", "ignore")
        fin.close()   # get the mimetype here
    except:
        print "Failed: %s" % url[:30]
        return None
    print "Scraped: %d bytes from %s" % (len(text), url[:30])
    return text

