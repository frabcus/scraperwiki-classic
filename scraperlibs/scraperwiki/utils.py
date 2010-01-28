__doc__ = """ScraperWiki Utils - to be replaced by proper urllib over-riding"""
__version__ = "ScraperWiki_0.0.1"

import urllib2
import urllib
import cookielib
import re
try:
  import json
except:
  import simplejson as json

import cgi
import os
import traceback
import datetime

# this will be useful for profiling the code, 
# it should return an output in json that you can click on to take you to the correct line
# see formatting in scrape 
def log(message=""):
    '''send message to console and the firebox logfile with a piece of the stack trace'''
    stack = traceback.extract_stack()
    tail = len(stack) >= 3 and ", %s() line %d" % (stack[-3][2], stack[-3][1]) or ""  # go 2 levels up if poss
    now = datetime.datetime.now()
    str_now = now.strftime("%Y-%m-%d %H:%M:%S")
    logmessage = "log( %s )\t\t %s() line %d%s : %s" % (str(message), stack[-2][2], stack[-2][1], tail, str_now)
    print logmessage
    

# these two functions scrape and parse are pretty much redundant, because everything worthwhile 
# is going to get done using mechanize

# global object handles cookies which work within the same session for now
# this will be formalized and made explicit when we make the urllib wrapping cache system
# that archives all the cookies for re-running the scraper code against
cj = cookielib.CookieJar()
urllibopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# over-ride the default value of [('User-agent', 'Mozilla/5.0')]
urllibopener.addheaders = [('User-agent', 'ScraperWiki - please make your data open :)')]


# should the exceptions be caught here?  
# should the print statements  go to different streams?
def scrape (url, params=None):
    '''get html text given url and parameter map'''
    data = params and urllib.urlencode(params) or None
    
    try:
        fin = urllibopener.open(url, data)
        text = unicode(fin.read(), errors="replace").encode("ascii", "ignore")
        fin.close()   # get the mimetype here
    except:
        print '<scraperwiki:message type="sources">' + json.dumps({ 'content' : "Failed: %s" % url })
        return None

    print_content = {
      'url': url,
      'content' : "%d bytes from %s" % (len(text), url),
      }
      #'content_long' : cgi.escape(text),      
    
    print '<scraperwiki:message type="sources">%s' % json.dumps(print_content)
    return text


# etree has many functions that apply to an etree._Element that are not in the Element, 
#  eg etree.tostring(element)


# the etree element object has following functions:
#   element.findall(".//span")          finds all span objects below the element
#   element.findall(".//span[@id]")     finds all span objects that have an id attribute (THIS DOESN'T WORK)
#   element.tag                         the tag of an element
#   element.getchildren()               list of children of an element
#   element.attrib                      dict of attributes and values
#   element.text                        plain text contents of element (for html contents, use etree.tostring(element)
def parse_html(text):
    """Turn some text into a lxml.etree object"""
    
    import lxml.etree as etree   # can't do as from lxml.etree import etree
    import html5lib
    
    tree = html5lib.treebuilders.getTreeBuilder("etree", etree)
    parser = html5lib.HTMLParser(tree=tree)
    rootelement = parser.parse(text)
    return rootelement


def pdftoxml(pdfdata):
    """converts pdf file to xml file"""
    import tempfile
    pdffout = tempfile.NamedTemporaryFile(suffix='.pdf')
    print pdffout.name
    pdffout.write(pdfdata)
    pdffout.flush()

    xmlin = tempfile.NamedTemporaryFile(mode='r', suffix='.xml')
    tmpxml = xmlin.name # "temph.xml"
    cmd = '/usr/bin/pdftohtml -xml -nodrm -zoom 1.5 -enc UTF-8 -noframes "%s" "%s"' % (pdffout.name, os.path.splitext(tmpxml)[0])
    cmd = cmd + " >/dev/null 2>&1" # can't turn off output, so throw away even stderr yeuch
    os.system(cmd)

    pdffout.close()
    #xmlfin = open(tmpxml)
    xmldata = xmlin.read()
    xmlin.close()
    return xmldata





