#!/usr/bin/env python

import os, sys, cgi, hashlib
import ConfigParser
import datetime, time
import socket
import traceback
import urllib
import traceback
import json

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
attachauthurl = config.get("dataproxy", 'attachauthurl')
resourcedir = config.get('dataproxy', 'resourcedir')

logging.config.fileConfig(configfile)
# port = config.getint('dataproxy', 'port')
logger = logging.getLogger('dataproxy')
logger.info("Serving twisted dataproxy now")
datalib.logger = logger

from twisted.python import log
from twisted.internet import reactor, protocol
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
        self.clienttype = ''
        self.attachauthurl = attachauthurl  # so it is available to datalib
        self.dbdeferredprocessing = False
        self.connectionlostwhiledeferredprocessing = False
        

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
        if self.dbdeferredprocessing:
            self.connectionlostwhiledeferredprocessing = True
                # connectionlost will be deferred
            # closing the connection to the database while the process is still going causes a segmentation fault in sqlite
        else:
            if self.db:
                self.db.close()
            self.factory.clientConnectionLost(self)

    def deferredConnectionLost(self):
        logger.info("connection client#%d deferredlost" % (self.clientnumber))
        self.db.close()
        self.factory.clientConnectionLost(self)

    # this will generalize to making status and other outputs from here
    def handlehttpgetresponse(self, path, params):
        self.transport.write('HTTP/1.0 200 OK\r\n')  
        self.transport.write('Connection: Close\r\n')  
        self.transport.write('Pragma: no-cache\r\n')  
        self.transport.write('Cache-Control: no-cache\r\n')  
        self.transport.write('Content-Type: text/text\r\n')  
        self.transport.write('\r\n')
        
        if path == "/status":
            self.transport.write('There are %d clients connected\n' % len(self.factory.clients))
        else:
            self.transport.write('Hello there\n')
        self.transport.loseConnection()
            
    # incoming to this connection
    def dataReceived(self, srec):
        ssrec = srec.split("\n")  # multiple strings if a "\n" exists
        self.sbufferclient.append(ssrec.pop(0))
        while ssrec:
            self.lineReceived(("".join(self.sbufferclient)).strip())
            self.sbufferclient = [ ssrec.pop(0) ]  # next one in

    # incoming to this connection
    def lineReceived(self, line):
            # even the socket connections are initialized with a GET line 
        if not self.clienttype:
            if line[:4] == 'GET ':
                self.clienttype = "httpget_headers"
                self.httpheaders = [ ]
            else:
                logger.warning("client#%d has connects with starting line: %s" % (self.clientnumber, line[:1000]))
                return
                
        if self.clienttype == "httpget_headers":
            if line:
                self.httpheaders.append(line.split(" ", (self.httpheaders and 1 or 2)))   # first line is GET /path?query HTTP/1.0
                logger.info("client#%d has headers: %s" % (self.clientnumber, str(self.httpheaders[-1])))
                return
            
        # the following is all triggered by the first blank line in the headers denoting the end of the header section
            logger.info("client#%d finished headers" % (self.clientnumber))
            path, q, query = self.httpheaders[0][1].partition("?")
            params = dict(cgi.parse_qsl(query))
            if not (path == '/' and params.get("uml") and len(self.httpheaders) == 1):
                logger.info("client#%d path '%s' params='%'" % (self.clientnumber, path, params.keys()))
                self.clienttype = "httpget_response"
                self.handlehttpgetresponse(path, params)
                return
               
            # directly from def do_GET (self) :
            self.verification_key = params['verify']

            self.dataauth = None
            self.attachables = params.get('attachables', '').split()
                    
            firstmessage = {"status":"good"}
            if 'short_name' in params:
                self.short_name = params.get('short_name', '')
                self.runID = 'fromfrontend.%s.%s' % (self.short_name, time.time()) 
                self.dataauth = "fromfrontend"
            else:
                self.runID, self.short_name = params.get('vrunid'), params.get("vscrapername", '')
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
                if self.runID != params.get('vrunid') or self.short_name != params.get("vscrapername", ''):
                    logger.error("Mismatching scrapername %s" % str([self.runID, self.short_name, params.get('vrunid'), params.get("vscrapername", '')]))
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
            self.db = datalib.SQLiteDatabase(self, resourcedir, self.short_name, self.dataauth, self.runID, self.attachables)

            self.clienttype = "dataproxy_socketmode"
            return
            
        # the main request response loop
        if self.clienttype == "dataproxy_socketmode":
            if line:
                try:
                    request = json.loads(line) 
                except ValueError, ve:
                    logger.error("%s; reading line '%s'" % (str(ve), line))
                    raise

                logger.debug("client#%d deferredrequest %s" % (self.clientnumber, str(request)[:100]))
                if self.dbdeferredprocessing:
                    logger.error("already doing deferredrequest!!!")
                    return
                    
                self.dbdeferredprocessing = True
                d = deferToThread(self.db.process, request)
                d.addCallback(self.db_process_success)
                d.addErrback(self.db_process_error)
            return
                
        logger.warning("client#%d Unhandled line: %s" % (self.clientnumber, line[:1000]))


    def db_process_success(self, res):
        self.dbdeferredprocessing = False
        logger.debug("client#%d success %s" % (self.clientnumber, str(res)[:100]))
        if self.connectionlostwhiledeferredprocessing:
            self.deferredConnectionLost()
        else:
            json.dump(res, self.transport)
            self.transport.write('\n')

    def db_process_error(self, failure):
        self.dbdeferredprocessing = False
        logger.warning("client#%d failure %s" % (self.clientnumber, str(failure)[:100]))
        if self.connectionlostwhiledeferredprocessing:
            self.deferredConnectionLost()
        else:
            self.transport.write(json.dumps({"error":"dataproxy.process: %s" % str(failure)})+'\n')        


class DatastoreFactory(protocol.ServerFactory):
    protocol = DatastoreProtocol
    
    def __init__(self):
        self.clients = [ ]   # all clients
        self.clientcount = 0
        
    def clientConnectionMade(self, client):
        client.clientnumber = self.clientcount
        self.clients.append(client)
        self.clientcount += 1
        
    def clientConnectionLost(self, client):
        if client in self.clients:
            logger.debug("removing client# %d" % (client.clientnumber))
            self.clients.remove(client)  # main list
        else:
            logger.error("No place to remove client %d" % client.clientnumber)

