import urllib

def ScrapeUrl(url):
    fin = urllib.urlopen(url)
    res = fin.read()
    return res

