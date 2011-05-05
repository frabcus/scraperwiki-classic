##!/bin/sh -
"exec" "python" "-O" "$0" "$@"

__doc__ = """ScraperWiki Data Proxy"""

__version__ = "ScraperWiki_0.0.1"

import BaseHTTPServer
import SocketServer
import urllib
import urlparse
import cgi
import select
import signal
import os
import sys
import time
import threading
import string 
import hashlib
import datalib
import ConfigParser
import datetime

try   : import json
except: import simplejson as json

global config

USAGE      = " [--varDir=dir] [--subproc] [--daemon] [--config=file]"
child      = None
config     = None
varDir     = '/var'
uid        = None
gid        = None

class ProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler) :

    """
    Proxy handler class. Overrides the base handler to implement
    filtering and proxying.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "DataProxy/" + __version__
    rbufsize       = 0

    def __init__ (self, *alist, **adict) :

        """
        Class constructor. All arguments (positional and keyed) are passed down to
        the base class constructor.
        """

        self.m_db      = None
        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

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


    def ident (self, uml, port) :

        """
        Request scraper and run identifiers, and host permissions from the UML.
        This uses local and remote port numbers to identify a TCP/IP connection
        from the scraper running under the controller.
        """

        scraperID   = None
        runID       = None
        scraperName = None

        #  Determin the caller host address and the port to call on that host from
        #  the configuration since the request will be from UML running inside that
        #  host (and note actually from the peer host). Similarly use the port
        #  supplied in the request since the peer port will have been subject to
        #  NAT or masquerading.
        #
        host      = config.get (uml, 'host')
        via       = config.get (uml, 'via' )
        rem       = self.connection.getpeername()
        loc       = self.connection.getsockname()
        ident     = urllib.urlopen ('http://%s:%s/Ident?%s:%s' % (host, via, port, loc[1])).read()   # (lucky this doesn't clash with the function we are in, eh -- JT)

                # would be a great idea to use cgi.parse_qs(query) technology here -- at both ends -- as it is already used in this module elsewhere!
        for line in string.split (ident, '\n') :
            if line == '' :
                continue
            key, value = string.split (line, '=')
            if key == 'runid'       :
                runID       = value
                continue
            if key == 'scraperid'   :
                scraperID   = value
                continue
            if key == 'scrapername' :
                scraperName = value
                continue

        return scraperID, runID, scraperName

    def postcodeToLatLng (self, db, scraperID, runID, postcode) :
        rc, arg = db.postcodeToLatLng (scraperID, postcode)
        self.connection.send (json.dumps ((rc, arg)) + '\n')

    def clear_datastore(self, db, scraperID, runID, scraperName):
        rc, arg = db.clear_datastore(scraperID, scraperName)
        self.connection.send(json.dumps ((rc, arg)) + '\n')


    def process (self, db, scraperID, runID, scraperName, request) :
        if request[0] == 'postcodetolatlng' :
            self.postcodeToLatLng (db, scraperID, runID, request[1])
            return

        if request[0] == 'clear_datastore':
            self.clear_datastore(db, scraperID, runID, scraperName)
            return

        # new experimental QD sqlite interface
        if request[0] == 'sqlitecommand':
            result = db.sqlitecommand(scraperID, runID, scraperName, command=request[1], val1=request[2], val2=request[3])
            self.connection.send(json.dumps(result) + '\n')
            return

        if request[0] == 'save_sqlite':
            result = db.save_sqlite(scraperID, runID, scraperName, unique_keys=request[1], data=request[2], swdatatblname=request[3])
            self.connection.send(json.dumps(result) + '\n')
            return
        
        self.connection.send (json.dumps ((False, 'Unknown datastore command: %s' % request[0])) + '\n')

    def do_GET (self) :

        """
        Handle GET request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        

        try    : params = urlparse.parse_qs(query)
        except : params = cgi     .parse_qs(query)

                # if the scraperid is set then we can assume it's from the frontend, is not authenticated and will have no write permissions
                # if it is not set, then it is fetched through the ident call and is then authenticated enough for writing purposes in its relevant file
        if 'scraperid' in params and params['scraperid'][0] not in [ '', None ] :
            if self.connection.getpeername()[0] != config.get ('dataproxy', 'secure') :
                self.connection.send (json.dumps ((False, "ScraperID only accepted from secure hosts")) + '\n')
                return
            scraperID, runID, scraperName = params['scraperid'][0], 'fromfrontend.%s.%s' % (params['scraperid'][0], time.time()), params.get('short_name', [""])[0]
        
        else :
            scraperID, runID, scraperName = self.ident (params['uml'][0], params['port'][0])


        if path == '' or path is None :
            path = '/'

        if scm not in [ 'http', 'https' ] or fragment :
            self.connection.send (json.dumps ((False, "Malformed URL %s" % self.path)) + '\n')
            return

        try    :
            db = datalib.Database(self)
            db.connect(config, scraperID)
        except Exception, e :
            self.connection.send (json.dumps ((False, '%s' % e)) + '\n')
            return

        self.connection.send(json.dumps ((True, 'OK')) + '\n')

        startat = time.strftime ('%Y-%m-%d %H:%M:%S')


                # enter the loop that now continues through until the connection is closed
                # unclear where self.connection is generated.  I believe it is a socket object
                # documentation on object is poor:  http://docs.python.org/release/2.5.2/lib/socket-objects.html
                # would be nice to obtain its error conditions, timeouts, and an explicit message that it is actually been closed
                # perhaps should be using sendall instead of send() everywhere
        sbuffer = [ ]
        try:
            while True:
                srec = self.connection.recv(255)
                ssrec = srec.split("\n")  # multiple strings if a "\n" exists
                sbuffer.append(ssrec.pop(0))
                while ssrec:
                    line = "".join(sbuffer)
                    if line:
                        request = json.loads(line) 
                        self.process(db, scraperID, runID, scraperName, request)
                    sbuffer = [ ssrec.pop(0) ]  # next one in
                if not srec:
                    break
                
        finally :
            self.connection.close()


    do_HEAD   = do_GET
    do_POST   = do_GET
    do_PUT    = do_GET
    do_DELETE = do_GET


class ProxyHTTPServer \
        (   SocketServer.ForkingMixIn,
            BaseHTTPServer.HTTPServer
        ) :
    pass


def execute (port) :

    ProxyHandler.protocol_version = "HTTP/1.0"

    httpd = ProxyHTTPServer(('', port), ProxyHandler)
    sa    = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."

    httpd.serve_forever()


def sigTerm (signum, frame) :

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove (varDir + '/run/dataproxy.pid')
    except : pass
    sys.exit (1)


if __name__ == '__main__' :

    subproc = False
    daemon  = False
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

        if arg == '--subproc' :
            subproc = True
            continue

        if arg == '--daemon' :
            daemon = True
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
            sys.stdout = open (varDir + '/log/dataproxy', 'a', 0)
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

        pf = open (varDir + '/run/dataproxy.pid', 'w')
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
                break

            sys.stdout.write("%s: Forked subprocess: %d\n" % (datetime.datetime.now().ctime(), child))
            sys.stdout.flush()
    
            os.wait()


    config = ConfigParser.ConfigParser()
    config.readfp (open(confnam))

    execute (config.getint ('dataproxy', 'port'))
