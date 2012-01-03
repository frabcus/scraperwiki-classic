#!/usr/bin/env python

import os, sys, cgi, hashlib
import ConfigParser
import datetime, time
import socket
import traceback
import urllib
import traceback
import json
import StringIO

import logging
import logging.config
try:
    import cloghandler
except:
    pass

import datalib

# note: there is a symlink from /var/www/scraperwiki to the scraperwiki directory
# which allows us to get away with being crap with the paths

configfile = '/var/www/scraperwiki/uml/uml.cfg'
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))
dataproxy_secret = config.get('dataproxy', 'dataproxy_secret')
datalib.attachauthurl = config.get("dataproxy", 'attachauthurl')
datalib.resourcedir = config.get('dataproxy', 'resourcedir')

logging.config.fileConfig(configfile)
# port = config.getint('dataproxy', 'port')
logger = logging.getLogger('dataproxy')
logger.info("Serving twisted dataproxy now")
datalib.logger = logger

from twisted.python import log
from twisted.internet import reactor, protocol, task
from twisted.protocols import basic
from twisted.internet import defer
from twisted.internet.threads import deferToThread

allowed_ips = ['127.0.0.1']

class DatastoreProtocol(protocol.Protocol):

    def __init__(self):
        self.clientnumber = -1         # number for whole operation of twisted
        self.clientsessionbegan = datetime.datetime.now()
        self.sbufferclient = [ ] # incoming messages from the client
        self.db = None
        self.Dattached = [ ] # attached function calls (for debug purposes)
        self.clienttype = 'justconnected'
        self.dbprocessrequest = None
        
        self.httpheaders = [ ]
        self.httpgetparams = {}
        self.httpgetpath = ''
        self.httppostbuffer = None
        

    def connectionMade(self):
        self.factory.clientConnectionMade(self)
        logger.info("connection client#%d" % self.clientnumber)
        try:
            socket = self.transport.getHandle()
            if not socket.getpeername()[0] in allowed_ips:
                logger.info('Refused connection from %s' % (socket.getpeername()[0],))                
                self.transport.loseConnection()
                return
        except Exception, e:
            raise e
        
    def connectionLost(self, reason):
        logger.info("connection client#%d lost reason:%s" % (self.clientnumber, reason))
        self.factory.clientConnectionLost(self)


    # this will generalize to making status and other outputs from here
    def handlehttpgetresponse(self):
        self.transport.write('HTTP/1.0 200 OK\r\n')  
        self.transport.write('Connection: Close\r\n')  
        self.transport.write('Pragma: no-cache\r\n')  
        self.transport.write('Cache-Control: no-cache\r\n')  
        self.transport.write('Content-Type: text/text\r\n')  
        self.transport.write('\r\n')
        
        if self.httpgetpath == "/status":
            self.transport.write('There are %d clients connected\n' % len(self.factory.clients))
        else:
            self.transport.write('Hello there\n')
        if self.httppostbuffer:
            self.transport.write('received post body size: %d\n' % len(self.httppostbuffer.getvalue()))
        self.transport.loseConnection()

    # directly from def do_GET (self) :
    def handlesocketmodefirstmessage(self):
        self.verification_key = self.httpgetparams['verify']

        self.dataauth = None
        self.attachables = self.httpgetparams.get('attachables', '').split()
                
        firstmessage = {"status":"good"}
        if 'short_name' in self.httpgetparams:
            self.short_name = self.httpgetparams.get('short_name', '')
            self.runID = 'fromfrontend.%s.%s' % (self.short_name, time.time()) 
            self.dataauth = "fromfrontend"
        else:
            self.runID, self.short_name = self.httpgetparams.get('vrunid'), self.httpgetparams.get("vscrapername", '')
            if not self.runID:
                firstmessage = {"error":"ident failed no runID"}
            elif self.runID[:8] == "draft|||" and self.short_name:
                self.dataauth = "draft"
            else:
                self.dataauth = "writable"

            logger.debug( '.%s.' % [self.short_name])
                # send back identification so we can compare against it (sometimes it doesn't quite work out)
            firstmessage["short_name"] = self.short_name
            firstmessage["runID"] = self.runID
            firstmessage["dataauth"] = self.dataauth

            # run verification of the names against what we identified
            if self.runID != self.httpgetparams.get('vrunid') or self.short_name != self.httpgetparams.get("vscrapername", ''):
                logger.error("Mismatching scrapername %s" % str([self.runID, self.short_name, self.httpgetparams.get('vrunid'), self.httpgetparams.get("vscrapername", '')]))
                firstmessage["error"] = "Mismatching scrapername from ident"
                firstmessage["status"] = "bad: mismatching scrapername from ident"
        
        # Copied from services/datastore/dataproxy.py
        # Check verification key on first run.
        logger.debug('Verification key is %s' % self.verification_key)
        secret_key = '%s%s' % (self.short_name, dataproxy_secret,)
        possibly = hashlib.sha256(secret_key).hexdigest()  
        logger.debug('Comparing %s == %s' % (possibly, self.verification_key) )
        if possibly != self.verification_key:
            firstmessage = {"error": "Permission denied"}

        # consolidate sending back to trap socket errors
        logger.debug(firstmessage)
        self.transport.write(json.dumps(firstmessage)+'\n')
        
        logger.debug("connection made to dataproxy for %s %s - %s" % (self.dataauth, self.short_name, self.runID))
        self.short_name_dbreadonly = (self.dataauth == "fromfrontend") or (self.dataauth == "draft" and self.short_name)
        self.clienttype = "dataproxy_socketmode"


    # incoming to this connection
    def dataReceived(self, srec):
        logger.info("rec: "+str([srec])[:200])
        self.sbufferclient.append(srec)
        while self.clienttype in ["justconnected", "httpget_headers", "dataproxy_socketmode"]:
            ssrec = self.sbufferclient[-1].split("\n", 1)  # multiple strings if a "\n" exists (\r precedes \n)
            if len(ssrec) == 1:
                return
            self.sbufferclient[-1] = ssrec[0]
            line = "".join(self.sbufferclient)
            self.sbufferclient = [ ssrec[1] ]
            self.lineReceived(line)
            
        if self.clienttype == 'httppostbody':
            while self.sbufferclient:
                self.httppostbuffer.write(self.sbufferclient.pop(0))
            logger.info("client#%d postbody current length: %d" % (self.clientnumber, self.httppostbuffer.tell()))
            if self.httpgetcontentlength == self.httppostbuffer.tell():
                self.handlehttpgetresponse()
                


    # incoming to this connection
    # even the socket connections from the uml are initialized with a GET line 
    def lineReceived(self, line):
        logger.info("--- %s %s" % (self.clienttype, line))
        if self.clienttype == 'justconnected':
            if line[:4] == 'GET ' or line[:5] == 'POST ':
                self.clienttype = "httpget_headers"
            else:
                logger.warning("client#%d has connects with starting line: %s" % (self.clientnumber, line[:1000]))
                
        if self.clienttype == "httpget_headers" and line.strip():
            self.httpheaders.append(line.strip().split(" ", (self.httpheaders and 1 or 2)))   # first line is GET /path?query HTTP/1.0
            logger.info("client#%d header: %s" % (self.clientnumber, str(self.httpheaders[-1])))
            
        elif self.clienttype == "httpget_headers":  # and not line
            logger.info("client#%d finished headers" % (self.clientnumber))
            self.httpgetpath, q, self.httpgetquery = self.httpheaders[0][1].partition("?")
            self.httpgetparams = dict(cgi.parse_qsl(self.httpgetquery))
            self.httpheadersmap = dict(self.httpheaders[1:])
            self.httpgetcontentlength = int(self.httpheadersmap.get('Content-Length:', '0'))
            
            if self.httpheaders[0][0] == 'POST' and self.httpgetcontentlength:
                self.clienttype = "httppostbody"
                self.httppostbuffer = StringIO.StringIO()
                logger.info("client#%d post body length: %d" % (self.clientnumber, self.httpgetcontentlength))
                    
            elif (self.httpheaders[0][0] == 'GET' and self.httpgetpath == '/' and self.httpgetparams.get("uml") and len(self.httpheaders) == 1):
                self.clienttype = 'dataproxy_socketmode_start'
                self.handlesocketmodefirstmessage()
                
            else:
                self.clienttype = "httpget_response"
                self.handlehttpgetresponse()
               
        # the main request response loop
        elif self.clienttype == "dataproxy_socketmode":
            try:
                request = json.loads(line) 
            except ValueError, ve:
                request = line
            if type(request) != dict:
                self.sendResponse({"error":'request must be dict', "content":str(request)[:200]})
            elif "maincommand" not in request:
                self.sendResponse({"error":'request must contain maincommand', "content":str(request)})
            elif request["maincommand"] == 'sqlitecommand' and request.get("command") == "attach":
                self.Dattached.append(request)
                self.sendResponse({"status":"attach dataproxy request no longer necessary"})
            elif request["maincommand"] == 'sqlitecommand' and request.get("command") == "commit":
                self.sendResponse({"status":"commit not necessary as autocommit is enabled"})
            elif self.db:
                self.sendResponse({"error":'already doing deferredrequest!!!'})
            elif self.dbprocessrequest:
                self.sendResponse({"error":'already waiting on a processrequest!!!'})
            else:
                self.dbprocessrequest = request
                self.factory.addwaitingclient(self)

        else:
            logger.warning("client#%d Unhandled lineReceived: %s" % (self.clientnumber, line[:1000]))

    def sendResponse(self, res):
        if "error" in res:
            logger.warning("client#%d error: %s" % (self.clientnumber, str(res)))
        json.dump(res, self.transport)
        self.transport.write('\n')


class DatastoreFactory(protocol.ServerFactory):
    protocol = DatastoreProtocol
    
    def __init__(self):
        self.clients = [ ]     # all clients
        self.clientcount = 0   # for clientnumbers
        self.clientswaitingforswconn = [ ]
        self.swsqliteconnections = [ ]
        
        self.lc = task.LoopingCall(self.processnextwaitingclient)
        self.lc.start(5)

    def addwaitingclient(self, client):
        logger.info("added waiting client")
        assert client not in self.clientswaitingforswconn
        self.clientswaitingforswconn.append(client)
        
    def processnextwaitingclient(self):
        logger.info("looping call %d" % len(self.clientswaitingforswconn))
        if not self.clientswaitingforswconn:
            return
            
        client = self.clientswaitingforswconn.pop(0)
        logger.info("process open on client#%d" % client.clientnumber)
        client.db = datalib.SQLiteDatabase(client.short_name, client.short_name_dbreadonly)
        client.db.Dclientnumber = client.clientnumber
        client.db.clientforresponse = client
        client.db.factory = client.factory
        d = deferToThread(client.db.process, client.dbprocessrequest)
        client.dbprocessrequest = None
        d.addCallback(client.db.db_process_success)
        d.addErrback(client.db.db_process_error)
        
    def releasedbprocess(self, db):
        if db.clientforresponse:
            db.clientforresponse.db = None
        db.close()
        db.Dclientnumber = -1

    def clientConnectionMade(self, client):
        client.clientnumber = self.clientcount
        self.clients.append(client)
        self.clientcount += 1
        
    def clientConnectionLost(self, client):
        if client.db:
            logger.debug("stillrunning clientdb client# %d" % (client.clientnumber))
            client.db.clientforresponse = None

        if client in self.clients:
            logger.debug("removing client# %d" % (client.clientnumber))
            self.clients.remove(client)  # main list
        else:
            logger.error("No place to remove client %d" % client.clientnumber)

        