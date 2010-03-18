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

USAGE      = " [--port=port] [--umlAddr=port@addr] [--varDir=dir] [--enqueue] [--subproc] [--daemon]"
child      = None
port       = 9000
umlAddr    = []
varDir	   = '/var'
enqueue	   = False
uid	   = None
gid	   = None

UMLList    = []
UMLLock    = None
UMLPtr	   = None

class UML :

    """
    Class used to represent an instance of a UML server
    """

    def __init__ (self, name, server, port, count) :

        """
        Class constructor. Passed the server name, address, port and
        scraper count.

        @type	name	: String
	@param	name	: Server name
        @type	server	: String
	@param	server	: Server address
        @type	port	: Integer
	@param	port	: Port number
        @type	count	: Integer
	@param	count	: Scraper count
        """

        self.m_name    = name
        self.m_server  = server
        self.m_port    = port
        self.m_config  = None
        self.m_count   = count
        self.m_free    = count
        self.m_closing = False
        self.m_status  = {}
        self.m_lock    = threading.Semaphore(count)
        self.m_next    = None

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

        @rtype		: String
        @return		: Server address as machine:port
        """

        return self.m_server

    def port (self) :

        """
        Get port number

        @rtype		: Integer
        @return		: Port number
        """

        return self.m_port

    def acceptable (self) :

        """
        Test if the server is acceptable for a specific request.
        Currently a stub.

        @rtype		: Bool
        @return		: True if server is acceptable
        """

        return not self.m_closing 

    def free (self) :

        """
        Check if the server is free.

        @rtype		: Bool
        @return		: True if server is free
        """

        return self.m_free > 0

    def active (self) :

        return self.m_free < self.m_count

    def acquire (self, status) :

        """
        Acquire (ie., lock) a UML server. Note that if this is called
        and the server is already locked, the thread will hang until the
        server is released. The status is stored in the status dictionary
        against a unique random UUD - the request identifier - which is
        returned. 

        @type	status	: Dictionary
	@param	status	: Status information
        @rtype		: UUID
        @return		: Request identifier
        """

        #  The status is marked as state=W(aiting) before the UML
        #  semephore is acquired, and changed to state=R(unning) after.
        #
        id = uuid.uuid4()
        self.m_status[id] = status
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

        @type	id	: UUID
	@param	id	: Status identifier
        @return	Bool	: True if UML should be closed
        """

        self.m_lock.release()
        self.m_free += 1
        del self.m_status[id]

        return self.m_closing and not self.active()

    def config (self, config) :

        """
        Append configuration information for this UML. Each configuration is
        appended as a line in the form \em key1=value1;key2=value2;...

        @type	config	: List
	@param	config	: Configuration list
        """

        config.append \
                (       "name=%s;server=%s;port=%d;count=%d;free=%d;closing=%s" % \
                        (       self.m_name,
				self.m_server,
                                self.m_port,
                                self.m_count,
                                self.m_free,
                                self.m_closing
                )       )
				

    def status (self, status) :

        """
        Append status information for this UML. Each request is appended
        as a line in the form \em key1=value1;key2=value2;...

        @type	status	: List
	@param	status	: Status list
        """

        for key, value in self.m_status.items() :
           status.append (string.join([ '%s=%s' % (k,v) for k, v in value.items()], ';'))

    def close (self) :

        self.m_closing = True


def allocateUML (queue = False, **status) :

    """
    Allocate a UML. Normally this returns failure if no UML is free, but if
    the \em queue argument is true, then the thread may hang until a UML is
    free. The function returns (None,None) if the allocation is refused.

    @type	queue	: Bool
    @param	queue	: Queue request if no UML is immediately free
    @type	status	: Dictionary (gathered keyed arguments)
    @param	status	: Request status information
    @rtype		: UML, UUID
    @return		: Allocated UML and request identifier
    """

    global UMLPtr
    global UMLLock

    #  The scan for a free and acceptable UML is protected by the main
    #  lock.
    #
    UMLLock.acquire()

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

    @type	uml	: UML
    @param	uml	: UML to release
    @type	id	: UUID
    @param	id	: Request identifier
    """

    global UMLList

    UMLLock.acquire ()
    closing = uml.release (id)

    if closing :
        UMLList = [ u for u in UMLList if u is not uml ]
        for i in range(len(UMLList)) :
            UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
        UMLPtr  = UMLList[0]

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

        self.m_toRemove	= []
        self.m_swlog	= None

        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

    def __del__ (self) :

        """
        Class destructor. Remove any files that are queued to be removed.
        """

        for name in self.m_toRemove :
            try    : os.remove (name)
            except : pass

    def swlog (self) :

        if self.m_swlog is None :
            import SWLogger
            self.m_swlog = SWLogger.SWLogger()
            self.m_swlog.connect ()

        return self.m_swlog

    def _connect_to (self, server, port, soc) :

        """
        Connect to host. If the connection fails then a 404 error will have been
        sent back to the client.

        @type	server	: String
	@param	server	: Server address
        @type	port	: Integer
	@param	port	: Port number
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

        @type	format	: String
        @param	format	: Format string
        @type	args	: List
        @param	args	: Arguments to format string
        """

        BaseHTTPServer.BaseHTTPRequestHandler.log_message (self, format, *args)
        sys.stderr.flush ()

    def fileToRemove (self, name) :

        """
        Add a file name to a list of names to remove, and return the name.
        These files will be removed when the connection closes down.

        @type	name	: String
	@param	name	: File name
	@rtype		: String
	@return		: File name
        """

        self.m_toRemove.append (name)

#    def allowed (self) :
#
#        allowed = ''
#        for name, value in self.headers.items() :
#            if name[:17] == 'x-addallowedsite-' :
#                allowed += value + '\n'
#        return allowed
#
#    def blocked (self) :
#
#        blocked = ''
#        for name, value in self.headers.items() :
#            if name[:17] == 'x-addblockedsite-' :
#                blocked += '!' + value + '\n'
#        return blocked

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

    def addUML (self, info) :

        """
        Add a new UML

        @type	info	: String
	@param	info	: New UML as name:port:address:count
        """

        uname, uport, uaddr, count = info.split(':')

        UMLLock.acquire()

        try :
            UMLList.append (UML(uname, uaddr, int(uport), int(count)))
            for i in range(len(UMLList)) :
                UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
            UMLPtr  = UMLList[0]
        except :
            pass

        UMLLock.release()
        self.sendConfig()

    def removeUML (self, name) :

        """
        Remove a UML or mark closing if in use

        @type	name	: String
        @param	name	: Name of UML to remove
        """

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

        #  If the UML is not active then it can be removed now and a
        #  report to this effect returned.
        #
        if not uml.active() :
            UMLList = [ u for u in UMLList if u is not uml ]
            for i in range(len(UMLList)) :
                UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])
            UMLPtr  = UMLList[0]
            UMLLock.release()
            self.sendOK ()
            self.connection.send  ('UML %s removed' % name)
            self.connection.send  ('\n')
            return

        #  If active then mark as closing and report such. No scrapers
        #  will be allocated to the UML and it will be removed when it
        #  is next inactive.
        #
        uml.close()
        UMLLock.release()
        self.sendOK ()
        self.connection.send  ('UML %s closing' % name)
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

        try    : scraperID  = self.headers['x-scraperid' ]
        except : scraperID  = None
        try    : testName   = self.headers['x-testname'  ]
        except : testName   = ''
        try    : runID      = self.headers['x-runid'     ]
        except : runID      = ''

        self.swlog().log (scraperID, runID, 'D.START', arg1 = self.path)

        if scm != 'http' or fragment or netloc :
            self.send_error (400, "bad url %s" % self.path)
            self.swlog().log (scraperID, runID, 'D.ERROR', arg1 = 'Bad URL', arg2 = self.path)
            return

        uml, id = allocateUML (enqueue, scraperID = scraperID, testName = testName)
        if uml is None :
            self.send_error (400, "No server free to run your scraper, please try again in a few minutes")
            self.swlog().log (scraperID, runID, 'D.ERROR', arg1 = 'No UML', arg2 = '%s' % (self.path))
            return

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                self.swlog().log (scraperID, runID, 'D.REQUEST')
                self._read_write (soc)

        finally :
            soc            .close()
            self.connection.close()

        self.swlog().log (scraperID, runID, 'D.END')
        releaseUML       (uml, id)

    def _read_write (self, soc, idle = 0x7ffffff) :

        """
        Copy data backl and forth between the client and the server.

        @type   soc     : Socket
        @param  soc     : Socket to server
        @type   idle    : Integer
        @param  idel	: Maximum idling time between data
        """

        iw    = [self.connection, soc]
        ow    = []
        count = 0
        pause = 5
        busy  = True
        while busy :
            count        += pause
            (ins, _, exs) = select.select(iw, ow, iw, pause)
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

    for arg in sys.argv[1:] :

        if arg in ('-h', '--help') :
            print "usage: " + sys.argv[0] + USAGE
            sys.exit (1)

        if arg[: 6] == '--uid='	:
            uid      = arg[ 6:]
            continue

        if arg[: 6] == '--gid='	:
            gid      = arg[ 6:]
            continue

        if arg[:7] == '--port=' :
            port = int(arg[7:])
            continue

        if arg[:10] == '--umlAddr=' :
            umlAddr += arg[10:].split(',')
            continue

        if arg[:10] == '--umlPort=' :
            umlPort = int(arg[10:])
            continue

        if arg[ :9] == '--varDir='  :
            varDir  = arg[ 9:]
            continue

        if arg == '--subproc' :
            subproc = True
            continue

        if arg == '--daemon'  :
            daemon  = True
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

    if len(umlAddr) == 0 :
        umlAddr.append ('uml001:9001:89.16.177.195:25')
        umlAddr.append ('uml002:9001:89.16.177.195:25')
        umlAddr.append ('uml003:9001:89.16.177.195:25')
        umlAddr.append ('uml004:9001:89.16.177.195:25')
#        umlAddr.append ('uml001:9101:89.16.177.195:25')
#        umlAddr.append ('uml002:9102:89.16.177.195:25')
#        umlAddr.append ('uml003:9103:89.16.177.195:25')
#        umlAddr.append ('uml004:9104:89.16.177.195:25')


    for e in umlAddr :
        uname, uport, uaddr, count = e.split(':')
        UMLList.append (UML(uname, uaddr, int(uport), int(count)))

    for i in range(len(UMLList)) :
        UMLList[i].setNextUML(UMLList[(i+1) % len(UMLList)])

    UMLPtr  = UMLList[0]
    UMLLock = threading.Lock()

    execute (port)
