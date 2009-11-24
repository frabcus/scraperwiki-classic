
import xml.dom.minidom
import xml.dom.minidom
import datetime
import re
import os

import sys, string
from xml.sax import handler, make_parser

import connection


class ParseXMLhandler(handler.ContentHandler):             
    def __init__(self, wpdump):
        self.level = 0
        self.pageNumber = 0
        self.charData = None
        self.url = "file://"+wpdump
        
        self.titleData = None
        self.textData = None
        self.timestampData = None
        
        self.conn = connection.Connection()
        self.c = self.conn.connect()
        
    def LoadPage(self, title, text, ttag):
        self.c.execute("REPLACE INTO `wikipediapages` (`title`,`text`,`ttag`) VALUES (%s, %s, %s);", 
                  (title, text, ttag))
    
    def startDocument(self):                                    
        print "--------  Document Start --------"
    def endDocument(self):
        print "Number of pages:", self.pageNumber
        print "--------  Document End --------"

    def startElement(self, name, attrs):                        
        if name == "page":
            self.pageNumber += 1
    
        self.level += 1
        if name == "page":
            self.pageNumber += 1
        elif name == "title":
            self.charData = self.titleData = [ ]
        elif name == "text":
            self.charData = self.textData = [ ]
        elif name == "timestamp":
            self.charData = self.timestampData = [ ]
                        

    def endElement(self, name):                                 
        self.charData = None
        self.level -= 1
        if self.level == 1 and name == "page":
            if self.pageNumber >= 100000:
                sys.exit(0)
            title = "".join(self.titleData)

            # #REDIRECT [[Norwich North (UK                         Parliament constituency)]]
            #if self.textData and re.match("\s*#REDIRECT", self.textData[0]):
            #    pass #print title, self.textData[0]
            
            ttag = "new"
            if re.search("\(UK Parliament constituency\)", title):
                ttag = "UK Parliament constituency"
                
            print self.pageNumber, title
            text = "".join(self.textData)
            timestamp = "".join(self.timestampData)
            if not re.match("\s*#REDIRECT(?i)", text):
                self.LoadPage(title, text, ttag)

        
    def characters(self, chrs):                                 
        if self.charData != None:
            self.charData.append(chrs.encode("utf8"))


def ParseXMLintoPages(wpdump):
    xmlhandler = ParseXMLhandler(wpdump)
    fin = open(wpdump)
    parser = make_parser()
    parser.setContentHandler(xmlhandler)
    parser.parse(fin)
    fin.close()

    
# get the files
fdir = "/home/goatchurch/scraperwiki/rawdatafiles"
for f in os.listdir(fdir):
    if re.search(".xml$", f):
        ParseXMLintoPages(os.path.join(fdir, f))
        

