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
import sys
import traceback
import datetime
import tempfile


import scraperwiki.console

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
    scraperwiki.console.logMessage (logmessage)


def httpresponseheader(headerkey, headervalue):
    ''' eg httpresponseheader('Content-Type', 'text/plain') '''
    scraperwiki.console.logHTTPResponseHeader (headerkey, headervalue)


#  The code will install a set of specific handlers to be used when a URL
#  is opened. See the "urllibSetup" and "urllib2Setup" functions below.
#
urllibopener  = None
urllib2cj     = None
urllib2opener = None
cacheFor      = 0

#  The "urllib2Setup" function is called with zero or more handlers. An opener
#  is constructed using these, plus a cookie processor, and is installed as the
#  urllib2 opener. The opener also overrides the user-agent header.
#
def urllib2Setup (*handlers) :

    global urllib2cj
    global urllib2opener
    urllib2cj = cookielib.CookieJar()
    urllib2opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(urllib2cj), *handlers)
    urllib2opener.addheaders = [('User-agent', 'ScraperWiki')]
    urllib2.install_opener (urllib2opener)

#  Similarly for urllib, but no handlers.
#
def urllibSetup () :

    global urllibopener
    urllibopener = urllib.URLopener()
    urllibopener.addheaders = [('User-agent', 'ScraperWiki')]
    urllib._urlopener = urllibopener

#  "allowCache" is called to allow (or disallow) caching; this will typically be
#  set True for running from the editor, and False when the scraped is cron'd
#
def allowCache (cf) :

    global cacheFor
    cacheFor = cf

#  API call from the scraper to enable caching, provided that it is allowed as in
#  the previous method. "urllibSetup" and "urllib2Setup" are called if they have
#  no already been called.
#
def cache (enable = True) :

#   global urllibopener
#   global urllib2opener

#   if urllibopener  is None : urllibSetup  ()
#   if urllib2opener is None : urllib2Setup ()
#   urllibopener .addheaders.append (('x-cache', enable and cacheFor or 0))
#   urllib2opener.addheaders.append (('x-cache', enable and cacheFor or 0))

    urllib2.urlopen("http://127.0.0.1:9001/Option?runid=%s&webcache=%s" % (os.environ['RUNID'], enable and cacheFor or 0)).read()

#  Scrape a URL optionally with parameters. This is effectively a wrapper around
#  urllib2.orlopen().
#
def scrape (url, params = None) :

    #  Normally the "urllib2Setup" function would have been called from
    #  the controller to specify http, https and ftp proxies, however check
    #  in case not and call without any handlers.
    #
    global urllib2opener
    if urllib2opener is None :
        urllib2Setup ()

    data = params and urllib.urlencode(params) or None

    fin  = urllib2opener.open(url, data)
    text = fin.read()
    fin.close()   # get the mimetype here

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
    pdffout = tempfile.NamedTemporaryFile(suffix='.pdf')
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


# code adapted from http://docs.python.org/library/imp.html#examples-imp
# ideally there is a way to seamlessly overload the __import__ function and get us to call out like this
# it should also be able to explicitly refer to a named revision
def swimport(name, swinstance="http://scraperwiki.com"):
    import imp
    try:
        return sys.modules[name]
    except KeyError:
        pass

    #fp, pathname, description = imp.find_module(name)
    url = "%s/editor/raw/%s" % (swinstance, name)
    modulecode = urllib.urlopen(url).read() + "\n"
    
    modulefile = tempfile.NamedTemporaryFile(suffix='.py')
    modulefile.write(modulecode)
    modulefile.flush()
    fp = open(modulefile.name)
    return imp.load_module(name, fp, modulefile.name, (".py", "U", 1))

class SWImporter(object):
    def __init__(self, swinstance="http://scraperwiki.com"):
        self.swinstance = swinstance

    def find_module(self, name, path=None):
        return self

    def load_module(self, name):
        try:
            return self.use_standard_import(name)
        except:
            return self.import_from_scraperwiki(name)

    def use_standard_import(self, name):
        return imp.load_module(imp.find_module(name))

    def import_from_scraperwiki(self, name):
        try:
            url = "%s/editor/raw/%s" % (self.swinstance, name)
            modulecode = urllib2.urlopen(url).read() + "\n"

            # imp.load_module really needs a file, cannot use StringIO
            modulefile = tempfile.NamedTemporaryFile(suffix='.py')
            modulefile.write(modulecode)
            modulefile.flush()

            with open(modulefile.name) as fp:
                return imp.load_module(name, fp, modulefile.name, (".py", "U", imp.PY_SOURCE))
        except:
            raise ImportError

# callback to a view with parameter lists (cross language capability)
def jsviewcall(name, **args):
    url = "http://scraperwiki.com/views/%s/run/?%s" % (name, urllib.urlencode(args))
    response = urllib.urlopen(url).read()
    try:
        return json.loads(response)
    except ValueError:
        return response
    
