#!/usr/bin/env python
# encoding: utf-8

"""
Does the initial loading of the databases.
"""

import connection
import sys

import xml.dom.minidom
import datetime
import re
import os

import sys, string
from xml.sax import handler, make_parser


class ParseXMLhandler(handler.ContentHandler):             
    def __init__(self, wpdump, c):
        self.level = 0
        self.pageNumber = 0
        self.charData = None
        self.url = "file://"+wpdump
        
        self.titleData = None
        self.textData = None
        self.timestampData = None
        
        self.c = c
        
    def LoadPage(self, title, text, ttag):
        self.c.execute("REPLACE INTO `wikipediapages` (`title`,`text`,`ttag`) VALUES (%s, %s, %s);", 
                  (title, text, ttag))
    
    def startDocument(self):                                    
        print "--------  Document Start --------"
    def endDocument(self):
        print "Number of pages:", self.pageNumber
        print "--------  Document End --------"

    def startElement(self, name, attrs):                        
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
            if re.match("\s*#REDIRECT(?i)", text):
                ttag = "REDIRECT"
            self.LoadPage(title, text, ttag)

        
    def characters(self, chrs):                                 
        if self.charData != None:
            self.charData.append(chrs.encode("utf8"))


def ParseXMLintoPages(wpdump, c):
    xmlhandler = ParseXMLhandler(wpdump, c)
    fin = open(wpdump)
    parser = make_parser()
    parser.setContentHandler(xmlhandler)
    parser.parse(fin)
    fin.close()

    
# get the files
def load_wikipediapages():
    conn = connection.Connection()
    c = conn.connect()
    fdir = conn.wikipedia_dir()
    for f in os.listdir(fdir):
        if re.search(".xml$", f):
            ParseXMLintoPages(os.path.join(fdir, f), c)
        


def load_scheme():
  """Executes the SQL in scheme.sql"""
  
  exit = "y"
  while exit.lower() != "n" or exit.lower() !="y":
    if len(exit) != 0 and exit.lower() != "y":
      print "%s IS NOT A VALID CHOICE" % exit.upper()
    exit = raw_input("""WARNING: 
        This will destroy any existing data that may be 
        in the database.  Do you want to continue?\n[N/y]:""")
    if len(exit) <= 0 or exit[0].lower() == "n":
      print "Exiting"
      sys.exit()
    elif exit.lower() == "y":
      print "dumping"
      conn = connection.Connection()
      c = conn.connect()
      f = open('scheme.sql', 'r')
      c.execute(f.read())
      c.close()
      
      conn = connection.Connection()
      c = conn.connect()
      c.execute("""INSERT INTO `sequences` VALUES(0);""")
      c.close()
      break
      
      
      
      
if __name__ == "__main__":
  load_scheme()
  load_wikipediapages()
 