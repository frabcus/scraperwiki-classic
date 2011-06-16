#!/usr/bin/env python

import BaseHTTPServer
import SocketServer
import socket
import urlparse
import select
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

try:
    import json
except:
    import simplejson as json

parser = optparse.OptionParser()
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--setuid", action="store_true")
parser.add_option("--monitor", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

#stdoutlog = open('/var/www/scraperwiki/uml/var/log/dispatcher.log'+"-stdout", 'a', 0)
stdoutlog = None

runningscrapers = { }   # maps runid => { scraperID, runID, short_name, uname, socket }

class UML(object):
    def __init__(self, uname, server, port, count):
        self.uname = uname
        self.server = server
        self.port = port
        self.count = count
        self.runids = set()
        self.livestatus = "live"  # or closing, or unresponsive

        self.logger = logging.getLogger('dispatcher')

    def is_available(self):
        if self.livestatus != "live":
            self.logger.debug("skipping uml %s with livestatus %s" % (self.uname, self.livestatus))
            return False
        elif len(self.runids) >= self.count:
            self.logger.debug("skipping uml %s with %d running on count %d" % (self.uname, len(self.runids), self.count))
            return False
        else:
            return True

    def is_empty(self):
        return len(self.runids) == 0

    def add_runid(self, runid):
        if len(self.runids) < self.count():
            self.runids.add(runid)
        else:
            raise 

    def status_url(self):
        return "http://%s:%s/Status" % (self.server, self.port)

    def status_line(self):
        return "name=%s;server=%s;port=%d;count=%d;runids=%d;livestatus=%s" % (self.uname,
                                                                               self.server,
                                                                               self.port,
                                                                               self.count,
                                                                               len(self.runids),
                                                                               self.livestatus)

class UnknownUMLException(Exception): pass
class DuplicateUMLException(Exception): pass

class UMLList(object):
    def __init__(self):
        self.logger = logging.getLogger('dispatcher')
        self.UMLLock = threading.Lock()
        self.UMLs = {} # maps uname => UML object

    def allocateUML(self, scraperstatus):
        self.UMLLock.acquire()

        umls = self.UMLs.values()
        uml = None
        while umls:
            uml = umls.pop(random.randint(0, len(umls)-1))
            if uml.is_available():
                scraperstatus["uname"] = uml.uname
                uml.add_runid(scraperstatus["runID"])
                runningscrapers[scraperstatus["runID"]] = scraperstatus
                break
            
        self.UMLLock.release()
        return uml

    def releaseUML(self, scraperstatus):
        self.logger.debug("uml %s releasing on: %s  %s" % (scraperstatus["uname"], scraperstatus["short_name"], scraperstatus["runID"]))
        uname = scraperstatus["uname"]
        
        self.UMLLock.acquire()
        uml = self.UMLs[uname]
        del runningscrapers[scraperstatus["runID"]]
        uml.runids.remove(scraperstatus["runID"])
        
        if uml.livestatus == "closing" and len(uml.runids) == 0:
            del self.UMLs[uname]
            self.logger.info('closing UML %s removed' % uname)
        
        self.UMLLock.release ()


    def addUML(self, uname):
        if not config.has_section(uname):
            raise UnknownUMLException()
        if uname in self.UMLs:
            raise DuplicateUMLException()

        host = config.get(uname, 'host')
        port = config.getint(uname, 'via')
        count = config.getint(uname, 'count')

        self.UMLLock.acquire()
        self.UMLs[uname] = UML(uname, host, port, count)
        self.UMLLock.release()

    def removeUML(self, uname):
        uml = self.get_uml(uname)

        self.UMLLock.acquire()
        if uml.is_empty():
            del self.UMLs[uname]
        else:
            uml.livestatus = "closing"
        self.UMLLock.release()

        return uml

    def get_config(self):
        sconfig = []
        for uml in self.UMLs.values():
            sconfig.append(uml.status_line())
        return '\n'.join(sconfig)

    def get_uml(self, uname):
        try:
            return self.UMLs[uname]
        except KeyError:
            raise UnknownUMLException()

    def values(self):
        return self.UMLs



class DispatcherHandler(BaseHTTPServer.BaseHTTPRequestHandler):

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
        config = self.server.uml_list.get_config()
        self.logger.debug("sendConfig: "+str(sconfig)[:20])
        self.connection.send(config)
        self.connection.send('\n')

        # this is interpreted by codewiki/management/commands/run_scrapers.GetDispatcherStatus
    def sendStatus(self):
        res = []
        for scraperstatus in runningscrapers.values():
            res.append('uname=%s;scraperID=%s;short_name=%s;runID=%s;runtime=%s' % \
                       (scraperstatus["uname"], scraperstatus["scraperID"], scraperstatus["short_name"], scraperstatus["runID"], time.time()-scraperstatus["time"]))
        self.logger.debug("sendStatus: "+str(res)[:20])
        
        self.connection.send('\n'.join(res))
        self.connection.send('\n')

    def addUML(self, uname):
        self.logger.info("addUML: '%s'" % uname)
        try:
            self.server.uml_list.addUML(uname)
        except UnknownUMLException:
            self.logger.warning("addUML on unknown uml: "+uname)
            self.connection.send('UML %s not found' % uname)
            self.connection.send('\n')
        except DuplicateUMLException:
            self.logger.warning("addUML on uml alread there: "+uname)
            self.connection.send('UML %s already present' % uname)
            self.connection.send('\n')
        
        self.sendConfig()


    def removeUML(self, uname):
        self.logger.info("removeUML: '%s'" % uname)

        try:
            uml = self.server.uml_list.removeUML(uname)
            if uml.livestatus == "closing":
                self.logger.info('UML %s closing' % uname)
                self.connection.send('UML %s closing' % uname)
            else:
                self.logger.info('UML %s removed' % uname)
                self.connection.send('UML %s removed' % uname)
            self.connection.send('\n')
        except UnknownUMLException:
            self.logger.warning("removeUML on unknown uml: "+uname)
            self.connection.send('UML %s not found' % uname)
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
            self.logger.info('Scraper %s killed on uname %s' % (runID, scraperstatus["uname"]))
            self.connection.send('Scraper %s killed' % runID)
        else:
            self.logger.warning('Scraper %s not found' % (runID))
            self.connection.send('Scraper %s not found'  % runID)
        self.connection.send('\n')


    def do_GET (self) :
        self.logger = logging.getLogger('dispatcher')
        try:
            scm, netloc, path, query, fragment = urlparse.urlsplit(self.path)
            self.sendConnectionHeaders()
            if path == '/Config':
                self.sendConfig()
            elif path == '/Status':
                self.sendStatus()
            elif path == '/Add':
                self.addUML(query)
            elif path == '/Remove':
                self.removeUML(query)
            elif path == '/Kill':
                self.killScraper(query)
            else:
                self.execute()
        except Exception, e:
            self.logger.exception("Uncaught exception in do_GET (path = %s): %s" % (path, e))
        finally:
            self.connection.close()


    def execute(self):
        # unpack the json packed up by runner.py
        remlength = int(self.headers['Content-Length'])
            # this is done with a recv in a loop in controller.  wonder whether rfile.read is more stable
        sdata = self.rfile.read(remlength)
        if len(sdata) != int(self.headers['Content-Length']):
            self.logger.error("failed to receive full record from runner")

        try:
            jdata = json.loads(sdata)
        except ValueError, e:
            self.logger.error("bad json value: %s: %s" % (str(e), sdata[:100]))
            return

        scraperID = jdata['scraperid']
        short_name = jdata['scrapername']
        runID = jdata['runid']

        assert runID not in runningscrapers
       
        scraperstatus = { 'scraperID':scraperID, 'runID':runID, 'short_name':short_name, 'time':time.time() }
        scraperstatus["connection"] = self.connection  # used to close it
        
        uml = self.server.uml_list.allocateUML(scraperstatus)
        if not uml:
            self.logger.error("no uml allocated for: %s  %s" % (short_name, runID))
            self.connection.sendall(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"No UML allocated"})+'\n')
            return

        self.logger.debug("uml %s allocated for execute on: %s  %s" % (scraperstatus["uname"], short_name, runID))
        
        # this is the first message sent back to runner.py
        json_msg = json.dumps({'message_type': 'executionstatus', 'content': 'startingrun', 'runID': runID, 'uml': scraperstatus["uname"]})
        self.connection.sendall(json_msg+'\n')

        # this is what connects to the controller
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        scraperstatus["socket"] = soc

        try:
            soc.connect((uml.server, uml.port))
        except socket.error, e:
            self.logger.warning("refused connection to uml %s" % uname)
            self.connection.sendall(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"Failed to connect to controller"})+'\n')
            self.server.uml_list.releaseUML(scraperstatus)
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
            self.logger.debug("into select %s" % (short_name))
            try:
                rback, wback, eback = select.select([soc, self.connection], [], [], 60)
            except select.error, e: 
                self.logger.warning("select error on %s" % (short_name))
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
                self.logger.exception("select socket.error %s" % (short_name))
                break
                
                
                
            if not rback:
                self.logger.debug("soft timeout on select.select for %s" % short_name)
                uml = self.server.uml_list.get_uml(scraperstatus["uname"])
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
                self.logger.debug("controller socket error: %s  %s" % (short_name, runID))
                rec = None
                
            if not rec:
                self.logger.debug("controller to dispatcher connection termination: %s  %s" % (short_name, runID))
                break
            self.logger.debug("done recv %s %s" % (short_name, [rec[:80]]))
            
            try:
                self.connection.sendall(rec)
            except socket.error, e:
                socketterminationmessage = "close for runner connection exception"
                break

        if socketterminationmessage:
            self.logger.debug("%s: %s  %s" % (socketterminationmessage, short_name, runID))
            try:
                soc.sendall(socketterminationmessage)   # any message sent to soc will cause the controller to close the process
            except socket.error, e:
                self.logger.warning("socket error on termination message %s" % (short_name))
        soc.close()
        
        self.server.uml_list.releaseUML(scraperstatus)

    do_HEAD   = do_GET
    do_POST   = do_GET
    do_PUT    = do_GET
    do_DELETE = do_GET


class UMLScanner(threading.Thread) :
    def __init__(self, url_list):
        threading.Thread.__init__ (self)
        self.logger = logging.getLogger('dispatcher')
        self.url_list = url_list

    def run(self):
        while True:
            time.sleep(10)

            # beware that things can change in lookup lists as we are using them, which is why copies are made before looping and get() is used to access
            umltimes = [ ]
            for uml in self.url_list.values():
                try:
                    stime = time.time()
                            # timeout of 2 secs is probably too severe (leave in for now to enable failure and testing)
                    res = urllib2.urlopen(url.status_url(), timeout=2).read()
                    umltimes.append("%.3f" % (time.time() - stime))
                    if uml.livestatus == "unresponsive":  # don't overwrite closing
                        self.logger.warning('unresponsive UML %s back to live' % uml.uname)
                        uml.livestatus = "live"
                except Exception, e:
                    if type(e) == TypeError:
                        self.logger.exception("wrong version of python?")
                    if uml.livestatus == "live":
                        self.logger.warning('UML %s now unresponsive while %d scrapers were running' % (uml.uname, len(uml.runids)))
                        uml.livestatus = "unresponsive"
                    elif uml.livestatus == "closing":
                        self.logger.warning('Closing UML %s unresponsive' % uml.uname)
                        
            self.logger.debug("uml response times: %s" % str(umltimes))

class DispatcherHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, *args, **kwargs):
        super(DispatcherHTTPServer, self).__init__(*args, **kwargs)
        self.uml_list = UMLList()

        for uname in config.get('dispatcher', 'umllist').split(',') :
            self.uml_list.addUML(uname)


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

    # Set the logging up after switching to nobody.nogroup
    logging.config.fileConfig(poptions.config)

    if poptions.monitor:
        mtr = UMLScanner()
        mtr.start()

    DispatcherHandler.protocol_version = "HTTP/1.0"
    httpd = DispatcherHTTPServer(('', config.getint('dispatcher', 'port')), DispatcherHandler)
    sa = httpd.socket.getsockname()
    logger = logging.getLogger('dispatcher')
    logger.info("Serving HTTP on %s port %s\n" % (sa[0], sa[1]))
    httpd.serve_forever()
