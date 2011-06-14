#!/usr/bin/env python

import BaseHTTPServer
import SocketServer
import socket
import urlparse
import select
import signal
import threading
import os
import sys
import time
import ConfigParser
import optparse
import pwd
import grp
import logging
import logging.config
try:
    import cloghandler
except:
    pass
import urllib2
import random

try    : import json
except : import simplejson as json

parser = optparse.OptionParser()
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--setuid", action="store_true")
parser.add_option("--monitor", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

logging.config.fileConfig(poptions.config)
logger = logging.getLogger('dispatcher')

#stdoutlog = open('/var/www/scraperwiki/uml/var/log/dispatcher.log'+"-stdout", 'a', 0)
stdoutlog = None

child = None

UMLLock = threading.Lock()

UMLs = { }              # maps uname => UML object
runningscrapers = { }   # maps runid => { scraperID, runID, short_name, uname, socket }

class UML:
    def __init__(self, uname, server, port, count):
        self.uname = uname
        self.server = server
        self.port = port
        self.count = count
        self.runids = set()
        self.livestatus = "live"  # or closing, or unresponsive


def allocateUML(scraperstatus):
    UMLLock.acquire()

    umls = UMLs.values()
    uml = None
    while umls:
        uml = umls.pop(random.randint(0, len(umls)-1))
        if uml.livestatus != "live":
            logger.debug("skipping uml %s with livestatus %s during allocation for  %s %s" % (uml.uname, uml.livestatus, scraperstatus["short_name"], scraperstatus["runID"]))
            uml = None
        elif len(uml.runids) >= uml.count:
            logger.debug("skipping uml %s with %d running on count %d during allocation for  %s %s" % (uml.uname, len(uml.runids), uml.count, scraperstatus["short_name"], scraperstatus["runID"]))
            uml = None
        else:
            break
    if uml:
        scraperstatus["uname"] = uml.uname
        uml.runids.add(scraperstatus["runID"])
        runningscrapers[scraperstatus["runID"]] = scraperstatus
        
    UMLLock.release()
    return uml

def releaseUML(scraperstatus):
    logger.debug("uml %s releasing on: %s  %s" % (scraperstatus["uname"], scraperstatus["short_name"], scraperstatus["runID"]))
    uname = scraperstatus["uname"]
    
    UMLLock.acquire()
    uml = UMLs[uname]
    del runningscrapers[scraperstatus["runID"]]
    uml.runids.remove(scraperstatus["runID"])
    
    if uml.livestatus == "closing" and len(uml.runids) == 0:
        del UMLs[uname]
        logger.info('closing UML %s removed' % uname)
    
    UMLLock.release ()


def addUML(uname):
    logger.info("addUML: '%s'" % uname)

    host = config.get(uname, 'host')
    port = config.getint(uname, 'via')
    count = config.getint(uname, 'count')

    assert uname not in UMLs
    UMLs[uname] = UML(uname, host, port, count)


class DispatcherHandler (BaseHTTPServer.BaseHTTPRequestHandler) :

    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "Dispatcher/ScraperWiki_0.0.1"
    rbufsize       = 0

    def sendConnectionHeaders(self):
        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')

    def sendConfig(self):
        sconfig = []
        for uml in UMLs.values()[:]:
            sconfig.append("name=%s;server=%s;port=%d;count=%d;runids=%d;livestatus=%s" % (uml.uname, uml.server, uml.port, uml.count, len(uml.runids), uml.livestatus))
        
        logger.debug("sendConfig: "+str(sconfig)[:20])
        self.connection.send('\n'.join(sconfig))
        self.connection.send('\n')

        # this is interpreted by codewiki/management/commands/run_scrapers.GetDispatcherStatus
    def sendStatus(self):
        res = []
        for scraperstatus in runningscrapers.values()[:]:
            res.append('uname=%s;scraperID=%s;short_name=%s;runID=%s;runtime=%s' % \
                       (scraperstatus["uname"], scraperstatus["scraperID"], scraperstatus["short_name"], scraperstatus["runID"], time.time()-scraperstatus["time"]))
        logger.debug("sendStatus: "+str(res)[:20])
        
        self.connection.send('\n'.join(res))
        self.connection.send('\n')

    def saddUML(self, uname):
        if not config.has_section(uname):
            logger.warning("addUML on unknown uml: "+uname)
            self.connection.send('UML %s not found' % uname)
            self.connection.send('\n')
            return
        if uname in UMLs:
            logger.warning("addUML on uml alread there: "+uname)
            self.connection.send('UML %s already present' % uname)
            self.connection.send('\n')
            return

        UMLLock.acquire()
        addUML(uname)
        UMLLock.release()
        
        self.sendConfig()

    def removeUML(self, uname):
        uml = UMLs.get(uname)
        if not uml:
            logger.warning("removeUML on unknown uml: "+uname)
            self.connection.send('UML %s not found' % uname)
            self.connection.send('\n')
            return

        logger.info("removeUML: '%s'" % uname)
        
        UMLLock.acquire()
        if len(uml.runids) == 0:
            del UMLs[uname]
        else:
            uml.livestatus = "closing"
        UMLLock.release()
            
        if uml.livestatus == "closing":
            logger.info('UML %s closing' % uname)
            self.connection.send('UML %s closing' % uname)
        else:
            logger.info('UML %s removed' % uname)
            self.connection.send('UML %s removed' % uname)
        self.connection.send('\n')


    def killScraper(self, runID):
        scraperstatus = runningscrapers.get(runID)
        if scraperstatus:
            scraperstatus["socket"].sendall("close for kill command")
                # if you close the socket here, then the select.select([socket]) will hang forever not getting any message from it
            # scraperstatus["socket"].close()  
                # closing this end however is consistent with select.select not hanging and should be used for the values running on unresponsive umls
            #scraperstatus["connection"].close()  
            

        if scraperstatus:
            logger.info('Scraper %s killed on uname %s' % (runID, scraperstatus["uname"]))
            self.connection.send('Scraper %s killed' % runID)
        else:
            logger.warning('Scraper %s not found' % (runID))
            self.connection.send('Scraper %s not found'  % runID)
        self.connection.send('\n')


    def do_GET (self) :
        try:
            scm, netloc, path, query, fragment = urlparse.urlsplit(self.path)
            self.sendConnectionHeaders()
            if path == '/Config':
                self.sendConfig()
            elif path == '/Status':
                self.sendStatus()
            elif path == '/Add':
                self.saddUML(query)
            elif path == '/Remove':
                self.removeUML(query)
            elif path == '/Kill':
                self.killScraper(query)
            else:
                self.execute()
        except Exception, e:
            logger.exception("Uncaught exception in do_GET (path = %s): %s" % (path, e))
        finally:
            self.connection.close()


    def execute(self):
        # unpack the json packed up by runner.py
        remlength = int(self.headers['Content-Length'])
            # this is done with a recv in a loop in controller.  wonder whether rfile.read is more stable
        sdata = self.rfile.read(remlength)
        if len(sdata) != int(self.headers['Content-Length']):
            logger.error("failed to receive full record from runner")

        try:
            jdata = json.loads(sdata)
        except ValueError, e:
            logger.error("bad json value: %s: %s" % (str(e), sdata[:100]))
            return

        scraperID = jdata['scraperid']
        short_name = jdata['scrapername']
        runID = jdata['runid']

        assert runID not in runningscrapers
       
        scraperstatus = { 'scraperID':scraperID, 'runID':runID, 'short_name':short_name, 'time':time.time() }
        scraperstatus["connection"] = self.connection  # used to close it
        
        uml = allocateUML(scraperstatus)
        if not uml:
            logger.error("no uml allocated for: %s  %s" % (short_name, runID))
            self.connection.sendall(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"No UML allocated"})+'\n')
            return

        logger.debug("uml %s allocated for execute on: %s  %s" % (scraperstatus["uname"], short_name, runID))
        
        # this is the first message sent back to runner.py
        json_msg = json.dumps({'message_type': 'executionstatus', 'content': 'startingrun', 'runID': runID, 'uml': scraperstatus["uname"]})
        self.connection.sendall(json_msg+'\n')

        # this is what connects to the controller
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        scraperstatus["socket"] = soc

        try:
            soc.connect((uml.server, uml.port))
        except socket.error, e:
            logger.warning("refused connection to uml %s" % uname)
            self.connection.sendall(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"Failed to connect to controller"})+'\n')
            releaseUML(scraperstatus)
            return

        if soc:
            soc.send('POST /Execute HTTP/1.1\r\n')
            soc.send('Content-Length: %s\r\n' % self.headers['Content-Length'])
            soc.send('Connection: close\r\n')
            soc.send("\r\n")
            soc.sendall(sdata)

            # this simply sends whatever chunks there are right back to runner without buffering them
            # if they were buffered then could detect the execution end json object and break in a timely manner here
            # rather than wait for the close or (more reliably) the shutdown signal to filter through (sometimes delayed).  
        socketterminationmessage = None
        while True:
            logger.debug("into select %s" % (short_name))
            try:
                rback, wback, eback = select.select([soc, self.connection], [], [], 60)
            except select.error, e: 
                logger.warning("select error on %s" % (short_name))
                try:
                    socketterminationmessage = "select error for %s was on soc" % (short_name)
                    select.select([soc], [], [], 0)
                    socketterminationmessage = "select error for %s was on connection" % (short_name)
                    select.select([self.connection], [], [], 0)
                    socketterminationmessage = "unexplained select error"
                except select.error, e: 
                    pass
                break
            except socket.error, e:
                socketterminationmessage = "select socket.error"
                logger.exception("select socket.error %s" % (short_name))
                break
                
                
                
            if not rback:
                logger.debug("soft timeout on select.select for %s" % short_name)
                uml = UMLs.get(scraperstatus["uname"])
                if not uml or uml.livestatus == "unresponsive":
                    socketterminationmessage = "close because uml %s unresponsive" % scraperstatus["uname"]
                    break
                continue
            
            if self.connection in rback:
                socketterminationmessage = "close for runner changed signal"
                break
            
            # incoming messages from the controller to relay forward
            assert soc in rback
            try:
                rec = soc.recv(8192)
            except socket.error:
                logger.debug("controller socket error: %s  %s" % (short_name, runID))
                rec = None
                
            if not rec:
                logger.debug("controller to dispatcher connection termination: %s  %s" % (short_name, runID))
                break
            logger.debug("done recv %s %s" % (short_name, [rec[:80]]))
            
            try:
                self.connection.sendall(rec)
            except socket.error, e:
                socketterminationmessage = "close for runner connection exception"
                break

        if socketterminationmessage:
            logger.debug("%s: %s  %s" % (socketterminationmessage, short_name, runID))
            try:
                soc.sendall(socketterminationmessage)   # any message sent to soc will cause the controller to close the process
            except socket.error, e:
                logger.warning("socket error on termination message %s" % (short_name))
        soc.close()
        
        releaseUML(scraperstatus)

    do_HEAD   = do_GET
    do_POST   = do_GET
    do_PUT    = do_GET
    do_DELETE = do_GET


class UMLScanner(threading.Thread) :
    def __init__(self):
        threading.Thread.__init__ (self)

    def run(self):
        while True:
            time.sleep(10)

            # beware that things can change in lookup lists as we are using them, which is why copies are made before looping and get() is used to access
            umltimes = [ ]
            for uml in UMLs.values():
                try:
                    stime = time.time()
                            # timeout of 2 secs is probably too severe (leave in for now to enable failure and testing)
                    res = urllib2.urlopen("http://%s:%s/Status" % (uml.server, uml.port), timeout=2).read()
                    umltimes.append("%.3f" % (time.time() - stime))
                    if uml.livestatus == "unresponsive":  # don't overwrite closing
                        logger.warning('unresponsive UML %s back to live' % uml.uname)
                        uml.livestatus = "live"
                except Exception, e:
                    if type(e) == TypeError:
                        logger.exception("wrong version of python?")
                    if uml.livestatus == "live":
                        logger.warning('UML %s now unresponsive while %d scrapers were running' % (uml.uname, len(uml.runids)))
                        uml.livestatus = "unresponsive"
                    elif uml.livestatus == "closing":
                        logger.warning('Closing UML %s unresponsive' % uml.uname)
                        
            logger.debug("uml response times: %s" % str(umltimes))

class DispatcherHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


def sigTerm(signum, frame):
    try:
        os.kill(child, signal.SIGTERM)
    except OSError:
        pass
    try:
        os.remove(poptions.pidfile)
    except OSError:
        pass
    sys.exit(1)


if __name__ == '__main__' :
    # daemon 
    if os.fork() == 0 :
        os.setsid()
        sys.stdin = open('/dev/null')
        if stdoutlog:
            sys.stdout = stdoutlog
            sys.stderr = stdoutlog
        if os.fork() == 0:
            ppid = os.getppid()
            while ppid != 1:
                time.sleep(1)
                ppid = os.getppid()
        else:
            os._exit(0)
    else:
        os.wait()
        sys.exit(1)

    pf = open(poptions.pidfile, 'w')
    pf.write('%d\n' % os.getpid())
    pf.close()

    if poptions.setuid:
        gid = grp.getgrnam("nogroup").gr_gid
        uid = pwd.getpwnam("nobody").pw_uid
        os.setregid(gid, gid)
        os.setreuid(uid, uid)

    # subproc mode
    signal.signal(signal.SIGTERM, sigTerm)
    while True:
        child = os.fork()
        if child == 0:
            time.sleep(1)
            break
        logger.info("Forked subprocess: %d\n" % child)
        os.wait()
        logger.warning("Forked subprocess ended: %d" % child)

    for uname in config.get('dispatcher', 'umllist').split(',') :
        addUML(uname)

    if poptions.monitor:
        mtr = UMLScanner()
        mtr.start()

    DispatcherHandler.protocol_version = "HTTP/1.0"
    httpd = DispatcherHTTPServer(('', config.getint('dispatcher', 'port')), DispatcherHandler)
    sa = httpd.socket.getsockname()
    logger.info("Serving HTTP on %s port %s\n" % (sa[0], sa[1]))
    httpd.serve_forever()
