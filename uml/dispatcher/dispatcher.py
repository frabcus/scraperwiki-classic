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

try    : import json
except : import simplejson as json

global config

USAGE   = " [--varDir=dir] [--enqueue] [--subproc] [--daemon] [--config=file] [--name=name] [--monitor]"
child   = None
umlAddr = []
varDir  = '/var'
config  = None
name    = 'dispatcher'
enqueue = False
uid     = None
gid     = None

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

    def setConfig (self, config) :

        self.m_config = config

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

    def config (self, config) :

        """
        Append configuration information for this UML. Each configuration is
        appended as a line in the form \em key1=value1;key2=value2;...

        @type   config  : List
        @param  config  : Configuration list
        """

        config.append \
                (       "name=%s;server=%s;port=%d;count=%d;free=%d;closing=%s;dead=%s" % \
                        (       self.m_name,
                                self.m_server,
                                self.m_port,
                                self.m_count,
                                self.m_free,
                                self.m_closing,
                                self.m_dead
                )       )
                

    def status (self, status) :

        """
        Append status information for this UML. Each request is appended
        as a line in the form \em key1=value1;key2=value2;...

        @type   status  : List
        @param  status  : Status list
        """

        for key, value in self.m_scrapers.items() :
           status.append (string.join([ '%s=%s' % (k,v) for k, v in value.m_status.items()], ';'))

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
            print >>sys.stderr, "http://%s:%s/Status" % (self.m_server, self.m_port)
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

    """
    Proxy handler class. Overrides the base handler to implement
    filtering and proxying.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "Dispatcher/" + __version__
    rbufsize       = 0

    def __init__ (self, *alist, **adict) :

        """
        Class constructor. All arguments (positional and keyed) are passed down to
        the base class constructor.
        """

        self.m_toRemove = []

        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

    def __del__ (self) :

        """
        Class destructor. Remove any files that are queued to be removed.
        """

        for name in self.m_toRemove :
            try    : os.remove (name)
            except : pass


    def _connect_to (self, server, port, soc) :

        """
        Connect to host. If the connection fails then a 404 error will have been
        sent back to the client.

        @type   server  : String
        @param  server  : Server address
        @type   port    : Integer
        @param  port    : Port number
        @return         : True if connected
        """

        try :
            soc.connect((server, port))
        except socket.error, arg:
            try    : msg = arg[1]
            except : msg = arg
            self.send_error (404, msg)
            return False

        return True

    def log_message (self, format, *args) :

        """
        Override this method so that we can flush stderr

        @type   format  : String
        @param  format  : Format string
        @type   args    : List
        @param  args    : Arguments to format string
        """

        BaseHTTPServer.BaseHTTPRequestHandler.log_message (self, format, *args)
        sys.stderr.flush ()

    def fileToRemove (self, name) :

        """
        Add a file name to a list of names to remove, and return the name.
        These files will be removed when the connection closes down.

        @type   name    : String
        @param  name    : File name
        @rtype          : String
        @return         : File name
        """

        self.m_toRemove.append (name)

    def sendOK (self) :

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')

    def sendConfig (self) :

        """
        Send configuration information.
        """

        #  Gather up the configuration information. Since we need to lock the UML
        #  structure for the duration, do this up front to make it as quick
        #  as possible.
        #
        config = []
        UMLLock.acquire()
        try    :
            for uml in UMLList :
                uml.config (config)
        except :
            pass
        UMLLock.release()

        self.sendOK ()
        self.connection.send  (string.join(config, '\n'))
        self.connection.send  ('\n')

    def sendStatus (self) :

        """
        Send status information.
        """

        #  Gather up the status information. Since we need to lock the UML
        #  structure for the duration, do this up front to make it as quick
        #  as possible.
        #
        status = []
        UMLLock.acquire()
        try    :
            for uml in UMLList :
                uml.status (status)
        except :
            pass
        UMLLock.release()

        self.sendOK ()
        self.connection.send  (string.join(status, '\n'))
        self.connection.send  ('\n')

    def addUML (self, name) :

        """
        Add a new UML

        @type   info    : String
        @param  info    : Name of UML to add
        """

        global UMLPtr
        global UMLList

        #  Check that the named UML exists, if not then report an
        #  error.
        #
        if not config.has_section (name) :
            self.sendOK ()
            self.connection.send  ('UML %s not found' % name)
            self.connection.send  ('\n')
            return

        #  Get the UML details and add to the list; the next UML
        #  pointer is arbitrarily reset to the first UML in the list
        #
        host  = config.get    (name, 'host' )
        via   = config.getint (name, 'via'  )
        count = config.getint (name, 'count')

        UMLLock.acquire()

        if name not in [uml.name() for uml in UMLList]:
            UMLList.append (UML(name, host, via, count))
            for i in range(len(UMLList)) :
                UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
            UMLPtr  = UMLList[0]

        UMLLock.release()

        #  On successful addition pass back the new configuration
        #  information.
        #
        self.sendConfig()

    def removeUML (self, name) :

        """
        Remove a UML or mark closing if in use

        @type   name    : String
        @param  name    : Name of UML to remove
        """

        global UMLPtr
        global UMLList

        #  Can UML list for the named UML, report an error it it is
        #  not found.
        #
        uml = None
        for i in range (len(UMLList)) :
            if UMLList[i].name() == name :
                uml = UMLList[i]
                break

        if uml is None :
            self.sendOK ()
            self.connection.send  ('UML %s not found' % name)
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
            self.sendOK ()
            self.connection.send  ('UML %s removed' % name)
            self.connection.send  ('\n')
        else:
        #  If active then mark as closing and report such. No scrapers
        #  will be allocated to the UML and it will be removed when it
        #  is next inactive.
        #
            uml.close()
            UMLLock.release()
            self.sendOK ()
            self.connection.send  ('UML %s closing' % name)
            self.connection.send  ('\n')

    def killScraper (self, runID) :

        """
        Kill a scraper

        @type   runID   : String
        @param  runID   : Run identifier
        """

        global UMLPtr
        global UMLList

        killed = None
        UMLLock.acquire()
        for uml in UMLList :
            killed = uml.killScraper (runID)
            if killed is not None :
                break
        UMLLock.release()
        self.sendOK ()
        if killed is True  : self.connection.send  ('Scraper %s killed'     % runID)
        if killed is False : self.connection.send  ('Scraper %s not killed' % runID)
        if killed is None  : self.connection.send  ('Scraper %s not found'  % runID)
        self.connection.send  ('\n')

    def do_GET (self) :

        """
        Handle GET request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')

        if path == '/Config' :
            self.sendConfig ()
            self.connection.close()
            return

        if path == '/Status' :
            self.sendStatus ()
            self.connection.close()
            return

        if path == '/Add'    :
            self.addUML     (query)
            self.connection.close()
            return

        if path == '/Remove' :
            self.removeUML  (query)
            self.connection.close()
            return

        if path == '/Kill'   :
            self.killScraper(query)
            self.connection.close()
            return

        try    : scraperID  = self.headers['x-scraperid' ]
        except : scraperID  = None
        try    : testName   = self.headers['x-testname'  ]
        except : testName   = ''
        try    : runID      = self.headers['x-runid'     ]
        except : runID      = ''


        if scm != 'http' or fragment or netloc :
            self.send_error (400, "bad url %s" % self.path)
            return

        uml, id = allocateUML (enqueue, scraperID = scraperID, runID = runID, testName = testName)
        if uml is None :
            self.send_error (400, "No server free to run your scraper, please try again in a few minutes")
            return

        self.connection.send \
            (   json.dumps \
                (   {   'message_type'  : 'executionstatus',
                        'content'       : 'startingrun',
                        'runID'         : runID,
                        'uml'           : uml.name()
                    }
                )   + '\n'
            )

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        uml.setSocket (id, soc)

        try :
            if self._connect_to (uml.server(), uml.port(), soc) :
                self.log_request(testName)
                soc.send \
                    (   "%s %s %s\r\n" %
                        (   self.command,
                            urlparse.urlunparse (('', '', path, params, query, '')),
                            self.request_version
                    )   )
                self.headers['Connection'] = 'close'
                del self.headers['Proxy-Connection']
                for name, value in self.headers.items() :
                    soc.send ("%s: %s\r\n" % (name, value))
                soc.send ("\r\n")
                self._read_write (soc)

        finally :
            soc            .close()
            self.connection.close()

        releaseUML       (uml, id)

    def _read_write (self, soc, idle = 0x7ffffff) :

        """
        Copy data backl and forth between the client and the server.

        @type   soc     : Socket
        @param  soc     : Socket to server
        @type   idle    : Integer
        @param  idel    : Maximum idling time between data
        """

        iw    = [self.connection, soc]
        ow    = []
        count = 0
        pause = 5
        busy  = True
        while busy :
            count        += pause
            try    :
                (ins, _, exs) = select.select(iw, ow, iw, pause)
            except :
                break
            if exs :
                break
            if ins :
                for i in ins :
                    if i is soc : out = self.connection
                    else        : out = soc
                    try    : data = i.recv (8192)
                    except : return
                    if data :
                        out.send(data)
                        count = 0
                    else :
                        busy = False
                        break
            if count >= idle :
                break

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
            print >>sys.stderr, "MONITOR"
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


def execute (port) :

    DispatcherHandler.protocol_version = "HTTP/1.0"

    httpd = DispatcherHTTPServer(('', port), DispatcherHandler)
    sa    = httpd.socket.getsockname()
    sys.stdout.write ("Serving HTTP on %s port %s\n" % ( sa[0], sa[1] ))
    sys.stdout.flush ()

    httpd.serve_forever()


def sigTerm (signum, frame) :

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove (varDir + '/run/dispatcher.pid')
    except : pass
    sys.exit (1)


if __name__ == '__main__' :

    subproc = False
    daemon  = False
    monitor = False
    confnam = 'uml.cfg'

    for arg in sys.argv[1:] :

        if arg in ('-h', '--help') :
            print "usage: " + sys.argv[0] + USAGE
            sys.exit (1)

        if arg[: 6] == '--uid=' :
            uid      = arg[ 6:]
            continue

        if arg[: 6] == '--gid=' :
            gid      = arg[ 6:]
            continue

        if arg[ :9] == '--varDir='  :
            varDir  = arg[ 9:]
            continue

        if arg[ :9] == '--config='  :
            confnam = arg[ 9:]
            continue

        if arg[ :7] == '--name='  :
            name    = arg[ 7:]
            continue

        if arg == '--subproc' :
            subproc = True
            continue

        if arg == '--daemon'  :
            daemon  = True
            continue

        if arg == '--monitor' :
            monitor = True
            continue

        if arg == '--enqueue' :
            enqueue = True
            continue

        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)


    #  If executing in daemon mode then fork and detatch from the
    #  controlling terminal. Basically this is the fork-setsid-fork
    #  sequence.
    #
    if daemon :

        if os.fork() == 0 :
            os .setsid()
            sys.stdin  = open ('/dev/null')
            sys.stdout = open (varDir + '/log/dispatcher', 'w', 0)
            sys.stderr = sys.stdout
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

        pf = open (varDir + '/run/dispatcher.pid', 'w')
        pf.write  ('%d\n' % os.getpid())
        pf.close  ()

    if gid is not None : os.setregid (int(gid), int(gid))
    if uid is not None : os.setreuid (int(uid), int(uid))

    #  If running in subproc mode then the server executes as a child
    #  process. The parent simply loops on the death of the child and
    #  recreates it in the event that it croaks.
    #
    if subproc :

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
    config = ConfigParser.ConfigParser()
    config.readfp (open(confnam))

    for uml in config.get (name, 'umllist').split(',') :
        host  = config.get    (uml, 'host' )
        via   = config.getint (uml, 'via'  )
        count = config.getint (uml, 'count')
        UMLList.append (UML(uml, host, via, count))

    for i in range(len(UMLList)) :
        UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])

    UMLPtr  = len(UMLList) > 0 and UMLList[0] or None
    UMLLock = threading.Lock()

    if monitor :

        mtr = UMLScanner ()
        mtr.start ()

    execute (config.getint (name, 'port'))
