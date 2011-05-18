#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

__doc__ = """ScraperWiki Dispatcher

Hacked by.                                      Mike Richardson
"""

__version__ = "ScraperWiki_0.0.1"

import BaseHTTPServer
import SocketServer
import select
import socket
import urlparse
import signal
import threading
import os
import sys
import time
import string
import uuid
import ConfigParser
import optparse
import pwd
import grp
import logging
import logging.config

try    : import json
except : import simplejson as json

global config

parser = optparse.OptionParser()
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--setuid", action="store_true")
parser.add_option("--monitor", action="store_true")
parser.add_option("--enqueue", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

logging.config.fileConfig(poptions.config)
logger = logging.getLogger('dispatcher')

#stdoutlog = open('/var/www/scraperwiki/uml/var/log/dispatcher.log'+"-stdout", 'a', 0)
stdoutlog = sys.stdout

child   = None
umlAddr = []

UMLList = []
UMLLock = None
UMLPtr  = None

class Scraper :

    def __init__ (self, status) :

        self.m_status = status
        self.m_socket = None

    def setSocket (self, socket) :

        self.m_socket = socket

    def runID (self) :

        return self.m_status['runID']

    def socket (self) :

        return self.m_socket

class UML :

    """
    Class used to represent an instance of a UML server
    """

    def __init__ (self, name, server, port, count) :

        """
        Class constructor. Passed the server name, address, port and
        scraper count.

        @type   name    : String
        @param  name    : Server name
        @type   server  : String
        @param  server  : Server address
        @type   port    : Integer
        @param  port    : Port number
        @type   count   : Integer
        @param  count   : Scraper count
        """

        self.m_name     = name
        self.m_server   = server
        self.m_port     = port
        self.m_config   = None
        self.m_count    = count
        self.m_free     = count
        self.m_closing  = False
        self.m_scrapers = {}
        self.m_lock     = threading.Semaphore(count)
        self.m_next     = None
        self.m_dead     = False

    def setNextUML (self, next) :

        self.m_next   = next

    def setConfig (self, lconfig) :

        self.m_config = lconfig

    def nextUML (self) :

        return self.m_next

    def name (self) :

        return self.m_name

    def server (self) :

        """
        Get server address

        @rtype      : String
        @return     : Server address as machine:port
        """

        return self.m_server

    def port (self) :

        """
        Get port number

        @rtype      : Integer
        @return     : Port number
        """

        return self.m_port

    def acceptable (self) :

        """
        Test if the server is acceptable for a specific request.
        Currently a stub.

        @rtype      : Bool
        @return     : True if server is acceptable
        """

        return not self.m_closing 

    def free (self) :

        """
        Check if the server is free.

        @rtype      : Bool
        @return     : True if server is free
        """

        if self.m_dead      : return False
        if self.m_free <= 0 : return False
        return True

    def active (self) :

        return self.m_free < self.m_count

    def dead(self):
        return self.m_dead

    def acquire (self, status) :

        """
        Acquire (ie., lock) a UML server. Note that if this is called
        and the server is already locked, the thread will hang until the
        server is released. The status is stored in the status dictionary
        against a unique random UUD - the request identifier - which is
        returned. 

        @type   status  : Dictionary
        @param  status  : Status information
        @rtype          : UUID
        @return         : Request identifier
        """

        #  The status is marked as state=W(aiting) before the UML
        #  semephore is acquired, and changed to state=R(unning) after.
        #
        id = uuid.uuid4()
        self.m_scrapers[id] = Scraper (status)
        status['state']   = 'W'
        status['name' ]   = self.m_name
        status['time' ]   = time.time()

        self.m_lock.acquire()
        self.m_free -= 1

        status['state']   = 'R'
        return id

    def release (self, id) :

        """
        Release (ie., unlock) a UML server. If another thread is hung on
        the lock then it will proceed. The status information is removed.

        @type   id  : UUID
        @param  id  : Status identifier
        @return Bool    : True if UML should be closed
        """

        self.m_lock.release()
        self.m_free += 1
        del self.m_scrapers[id]

        return self.m_closing and not self.active()

    def getconfigstatus(self):
        return "name=%s;server=%s;port=%d;count=%d;free=%d;closing=%s;dead=%s" % (self.m_name, self.m_server, self.m_port, self.m_count, self.m_free, self.m_closing, self.m_dead)

    def getstatuslist(self):
        res = [ ]
        for key, value in self.m_scrapers.items() :
            res.append(';'.join([ '%s=%s' % (k,v) for k, v in value.m_status.items()]))
        return res
        # The above output is interpreted in web/codewiki/management/commands/run_scrapers.py by
        # splitting on ; and then =. Doing it this way means that m_status can be used to accumulate
        # information without needing the code here to be changed.

    def close (self) :

        self.m_closing = True

    def setSocket (self, id, socket) :

        self.m_scrapers[id].setSocket (socket)

    def killScraper (self, runID) :

        for key, scraper in self.m_scrapers.items() :
            if scraper.runID() == runID :
                try    :
                    scraper.socket().close()
                    return True
                except :
                    return False
        return None

    def killAll (self) :

        for key, scraper in self.m_scrapers.items() :
            try    : scraper.socket().close()
            except : pass

    def scan (self) :

        try    :
            import urllib2
            res = urllib2.urlopen("http://%s:%s/Status" % (self.m_server, self.m_port), timeout = 2).read()
            self.m_dead = False
            return
        except :
            pass
        self.m_dead = True
        self.killAll ()


def allocateUML (queue = False, **status) :

    """
    Allocate a UML. Normally this returns failure if no UML is free, but if
    the \em queue argument is true, then the thread may hang until a UML is
    free. The function returns (None,None) if the allocation is refused.

    @type   queue   : Bool
    @param  queue   : Queue request if no UML is immediately free
    @type   status  : Dictionary (gathered keyed arguments)
    @param  status  : Request status information
    @rtype          : UML, UUID
    @return         : Allocated UML and request identifier
    """

    global UMLPtr
    global UMLLock

    #  The scan for a free and acceptable UML is protected by the main
    #  lock.
    #
    UMLLock.acquire()

    #  Special case, no UMLs available at all
    #
    if UMLPtr is None :
        UMLLock.release()
        return None, None

    #  First scan for a UML which is both acceptable and free. If found
    #  the acquire it and return it. The main lock is released.
    #
    uml = UMLPtr
    while True :
        if uml.acceptable() and uml.free() :
            id = uml.acquire(status)
            UMLLock.release()
            UMLPtr = uml.nextUML()
            return uml, id
        uml = uml.nextUML()
        if uml is UMLPtr :
            break

    #  If the first scan fails, and the \em queue option is enabled, then
    #  then simply look for an acceptable UML, and acquire it. The thread
    #  will hang until the UML is released.
    #
    if queue :
        uml = UMLPtr
        while True :
            if uml.acceptable() :
                id = uml.acquire(status)
                UMLLock.release()
                UMLPtr = uml.nextUML()
                return uml, id
            uml = uml.nextUML()
            if uml is UMLPtr :
                break

    #  Nothing doing, release the main lock and return failure.
    #
    UMLLock.release()
    return None, None

def releaseUML (uml, id) :

    """
    Release a UML

    @type   uml : UML
    @param  uml : UML to release
    @type   id  : UUID
    @param  id  : Request identifier
    """

    global UMLList

    UMLLock.acquire ()
    closing = uml.release (id)

    if closing :
        UMLList = [ u for u in UMLList if u is not uml ]
        for i in range(len(UMLList)) :
            UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
        UMLPtr  = len(UMLList) > 0 and UMLList[0] or None

    UMLLock.release ()


class DispatcherHandler (BaseHTTPServer.BaseHTTPRequestHandler) :

    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "Dispatcher/" + __version__
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
        UMLLock.acquire()
        try:
            for uml in UMLList:
                sconfig.append(uml.getconfigstatus())
        except:
            logger.exception("sendConfig")
        UMLLock.release()
        logger.debug("sendConfig: "+str(sconfig)[:20])

        self.sendConnectionHeaders()
        self.connection.send('\n'.join(sconfig))
        self.connection.send('\n')

    def sendStatus(self):
        sstatus = []
        UMLLock.acquire()
        try:
            for uml in UMLList:
                sstatus.extend(uml.getstatuslist())
        except:
            logger.exception("sendStatus")
        UMLLock.release()
        logger.debug("sendStatus: "+str(sstatus)[:20])
        
        self.sendConnectionHeaders()
        self.connection.send('\n'.join(sstatus))
        self.connection.send('\n')

    def addUML(self, uname):
        logger.info("addUML: '%s'" % uname)
        if not config.has_section(uname):
            logger.warning("addUML on unknown uml: "+uname)
            self.sendConnectionHeaders()
            self.connection.send('UML %s not found' % uname)
            self.connection.send('\n')
            return
        
        global UMLPtr
        global UMLList

        host  = config.get    (uname, 'host' )
        via   = config.getint (uname, 'via'  )
        count = config.getint (uname, 'count')

        UMLLock.acquire()
        if uname not in [uml.name() for uml in UMLList]:
            UMLList.append (UML(uname, host, via, count))
            for i in range(len(UMLList)) :
                UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
            UMLPtr = UMLList[0]
        UMLLock.release()
        
        self.sendConfig()

    def removeUML(self, uname):
        logger.info("removeUML: '%s'" % uname)
        global UMLPtr
        global UMLList

        uml = None
        for i in range (len(UMLList)):
            if UMLList[i].name() == uname:
                uml = UMLList[i]
                break

        if uml is None :
            logger.warning("removeUML on unknown uml: "+uname)
            self.sendConnectionHeaders()
            self.connection.send  ('UML %s not found' % uname)
            self.connection.send  ('\n')
            return

        UMLLock.acquire()

        #  If the UML is not active or it is dead then it can be removed now 
        #  and a report to this effect returned.
        #
        if not uml.active() or uml.dead():
            UMLList = [ u for u in UMLList if u is not uml ]
            for i in range(len(UMLList)) :
                UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
            UMLPtr  = len(UMLList) > 0 and UMLList[0] or None
            UMLLock.release()
            self.sendConnectionHeaders()
            self.connection.send  ('UML %s removed' % uname)
            self.connection.send  ('\n')
        
        #  If active then mark as closing and report such. No scrapers
        #  will be allocated to the UML and it will be removed when it
        #  is next inactive.
        #
        else:
            uml.close()
            UMLLock.release()
            self.sendConnectionHeaders()
            self.connection.send  ('UML %s closing' % uname)
            self.connection.send  ('\n')

    
    def killScraper(self, runID):
        global UMLPtr
        global UMLList

        killed = None
        UMLLock.acquire()
        for uml in UMLList :
            killed = uml.killScraper(runID)
            if killed is not None :
                break
        UMLLock.release()
        self.sendConnectionHeaders()
        if killed is True  : self.connection.send  ('Scraper %s killed'     % runID)
        if killed is False : self.connection.send  ('Scraper %s not killed' % runID)
        if killed is None  : self.connection.send  ('Scraper %s not found'  % runID)
        self.connection.send  ('\n')


    def do_GET (self) :
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        if path == '/Config' :
            self.sendConfig()
        elif path == '/Status' :
            self.sendStatus()
        elif path == '/Add'    :
            self.addUML(query)
        elif path == '/Remove' :
            self.removeUML(query)
        elif path == '/Kill'   :
            self.killScraper(query)
        else:
            if scm != 'http' or fragment or netloc:
                self.send_error(400, "bad url %s" % self.path)
            else:
                self.sendConnectionHeaders()
                self.execute(path, params, query)
        self.connection.close()


    def execute(self, path, params, query):
        # unpack the json packed up by runner.py
        sdata = self.rfile.read(int(self.headers['Content-Length']))
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

        logger.debug("execute on: %s  %s" % (short_name, runID))
        
        uml, id = allocateUML(poptions.enqueue, scraperID = scraperID, runID=runID, testName=short_name)
        if not uml:
            logger.error("no uml allocated for: %s  %s" % (short_name, runID))
            self.connection.send(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"No UML allocated"}))
            return


        # this is what we send back to runner.py
        json_msg = json.dumps({'message_type': 'executionstatus', 'content': 'startingrun', 'runID': runID, 'uml': uml.name()}) + '\n'
        self.connection.send(json_msg)

        # this is what connects to the controller
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        uml.setSocket(id, soc)

        try:
            soc.connect((uml.server(), uml.port()))
        except socket.error, e:
            logger.exception("execute")
            self.connection.send(json.dumps({'message_type': 'executionstatus', 'content': 'runcompleted', 'exit_status':"Failed to connect to controller"}))
            soc = None

        if soc:
            soc.send("%s %s %s\r\n" % (self.command, urlparse.urlunparse(('', '', path, params, query, '')), self.request_version))
            soc.send('Content-Length: %s\r\n' % self.headers['Content-Length'])
            soc.send('Connection: close\r\n')
            soc.send("\r\n")
            soc.send(sdata)

        while soc:
            rec = soc.recv(8192)
            if rec:
                try:
                    self.connection.send(rec)
                except socket.error, e:
                    soc.close()
                    soc = None
                    logger.debug("dispatcher to runner connection error")
            else:
                soc = None

        releaseUML(uml, id)


    do_HEAD   = do_GET
    do_POST   = do_GET
    do_PUT    = do_GET
    do_DELETE = do_GET


class UMLScanner (threading.Thread) :

    def __init__ (self) :

        threading.Thread.__init__ (self)

    def run (self) :

        global UMLPtr
        global UMLLock

        while True :
            time.sleep(10)
            UMLLock.acquire()
            if UMLPtr is None :
                UMLLock.release()
                continue
            umlList = []
            uml = UMLPtr
            while True :
                umlList.append (uml)
                uml = uml.nextUML()
                if uml is UMLPtr :
                    break
            UMLLock.release()
            for uml in umlList :
                uml.scan ()


class DispatcherHTTPServer \
        (   SocketServer.ThreadingMixIn,
            BaseHTTPServer.HTTPServer
        ) :
    pass


def sigTerm(signum, frame):
    os.kill (child, signal.SIGTERM)
    try:
        os.remove(poptions.pidfile)
    except OSError:
        pass
    sys.exit(1)


if __name__ == '__main__' :
    #  If executing in daemon mode then fork and detatch from the
    #  controlling terminal. Basically this is the fork-setsid-fork
    #  sequence.
    #
    if os.fork() == 0 :
        os.setsid()
        sys.stdin = open('/dev/null')
        sys.stdout = stdoutlog
        sys.stderr = stdoutlog
        if os.fork() == 0 :
            ppid = os.getppid()
            while ppid != 1 :
                time.sleep (1)
                ppid = os.getppid()
        else :
            os._exit (0)
    else :
        os.wait()
        sys.exit (1)

    pf = open(poptions.pidfile, 'w')
    pf.write  ('%d\n' % os.getpid())
    pf.close  ()

    if poptions.setuid:
        args.append('--uid=%d' % pwd.getpwnam("nobody").pw_uid)
        args.append('--gid=%d' % grp.getgrnam("nogroup").gr_gid)

    #  If running in subproc mode then the server executes as a child
    #  process. The parent simply loops on the death of the child and
    #  recreates it in the event that it croaks.
    #
    signal.signal (signal.SIGTERM, sigTerm)
    while True :

        child = os.fork()
        if child == 0 :
            time.sleep (1)
            break

        sys.stdout.write("Forked subprocess: %d\n" % child)
        sys.stdout.flush()

        os.wait()

    #  The dispatcher section of the config file contains the port number
    #  and the list of UMLs that this dispatcher controls; the access details
    #  for the UMLs is taken from the corresponding UML sections.
    #
    for uml in config.get ('dispatcher', 'umllist').split(',') :
        host  = config.get    (uml, 'host' )
        via   = config.getint (uml, 'via'  )
        count = config.getint (uml, 'count')
        UMLList.append (UML(uml, host, via, count))

    for i in range(len(UMLList)) :
        UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])

    UMLPtr  = len(UMLList) > 0 and UMLList[0] or None
    UMLLock = threading.Lock()

    if poptions.monitor:
        mtr = UMLScanner ()
        mtr.start ()

    DispatcherHandler.protocol_version = "HTTP/1.0"
    httpd = DispatcherHTTPServer(('', config.getint ('dispatcher', 'port')), DispatcherHandler)
    sa    = httpd.socket.getsockname()
    sys.stdout.write ("Serving HTTP on %s port %s\n" % ( sa[0], sa[1] ))
    sys.stdout.flush ()
    httpd.serve_forever()
