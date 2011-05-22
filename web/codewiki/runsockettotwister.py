from django.conf import settings
from codewiki import models
import frontend
import urllib
import re
import base64
import cgi
import ConfigParser
import socket

try:                import json
except ImportError: import simplejson as json

config = ConfigParser.ConfigParser()
config.readfp(open(settings.CONFIGFILE))

class RunnerSocket:
    def __init__(self, scraper, rev, query_string):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.jsonsbuffer = [ ]
        self.jsonoutputlist = [ ]
        
        self.soc.connect(("127.0.0.1", config.getint("twister", "port")))
        
        data = { "command":'connection_open', "guid":scraper.guid, 
                 "username":"DJANGOFRONTEND", "userrealname":"DJANGOFRONTEND", 
                 "language":scraper.language, "scrapername":scraper.short_name, 
                 "isstaff":True }
        self.soc.send(json.dumps(data)+"\r\n") 
        jdata = self.next()
        cdata = json.loads(jdata)
        #return json.loads(jdata)
        assert cdata["message_type"] == "editorstatus"
        print "loggedineditors ", cdata["loggedineditors"]

        rdata = { "command":"run", "guid":scraper.guid, 
                  "username":"DJANGOFRONTEND", "userrealname":"DJANGOFRONTEND", 
                  "language":scraper.language, "scrapername":scraper.short_name, 
                  "code":scraper.saved_code(rev), "urlquery":query_string 
                }
        self.soc.send(json.dumps(rdata)+"\r\n") 


        # incoming messages from twister are delimited by ",\r\n"
    def next(self):
        while not self.jsonoutputlist:
            srecjsons = self.soc.recv(8192)
            if not srecjsons:
                raise StopIteration  # maybe log the leftovers in self.jsonsbuffer
            ssrecjsons = srecjsons.split(",\r\n")
            self.jsonsbuffer.append(ssrecjsons.pop(0))
            while ssrecjsons:
                self.jsonoutputlist.append("".join(self.jsonsbuffer))
                del self.jsonsbuffer[:]
                self.jsonsbuffer.append(ssrecjsons.pop(0))
            
        jdata = self.jsonoutputlist.pop(0)
        data = json.loads(jdata)
        if data.get("message_type") == "executionstatus" and data.get("content") == "runfinished":
            self.soc.close()
            raise StopIteration 
        return jdata

    def __iter__(self):
        return self

    def readline(self):
        try:
            return self.next()
        except StopIteration:
            return ""
        

