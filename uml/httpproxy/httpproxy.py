##!/bin/sh -
"exec" "python" "-O" "$0" "$@"

__doc__ = """ScraperWiki HTTP Proxy"""

__version__ = "ScraperWiki_0.0.1"

import  BaseHTTPServer
import  SocketServer
import  select
import  socket
import  urlparse
import  signal
import  os
import  sys
import  time
import  threading
import  string 
import  urllib   # should this be urllib2? -- JGT
import  ConfigParser
import  hashlib

global config

USAGE       = " [--allowAll] [--varDir=dir] [--subproc] [--daemon] [--config=file] [--useCache]"
child       = None
config      = None
varDir      = '/var'
useCache    = False
uid         = None
gid         = None
allowAll    = False
statusLock  = None
statusInfo  = {}


class HTTPProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler) :

    """
    Proxy handler class. Overrides the base handler to implement
    filtering and proxying.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "HTTPProxy/" + __version__
    rbufsize       = 0

    def __init__ (self, *alist, **adict) :

        """
        Class constructor. All arguments (positional and keyed) are passed down to
        the base class constructor.
        """

        self.m_swlog   = None
        self.m_allowed = []
        self.m_blocked = []
        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

    def swlog (self) :

        if self.m_swlog is None :
            import swlogger
            self.m_swlog = swlogger.SWLogger(config)
            self.m_swlog.connect ()

        return self.m_swlog

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

    def hostAllowed (self, path, scraperID, runID) :

        """
        See if access to a specified host is allowed. These are specified as a list
        of regular expressions stored in a file; the expressions will be anchored at
        both start and finish so they must match the entire host. The file is named
        from the IP address of the caller.

        @type   path     : String
        @param  path     : Hostname
        @type   scraperID: String
        @param  scraperID: Scraper identifier or None
        @return          : True if access is allowed
        """

        import re

        if allowAll :
            return True

        allowed = False
        
        # first if it is the white-list
        for allow in self.m_allowed :
            if re.match(allow, path) :
                allowed = True
        
        # but not if it is in the black-list
        for block in self.m_blocked :
            if re.match(block, path) :
                allowed = False

        return allowed

    def _connect_to (self, netloc, soc) :

        """
        Connect to host. If the connection fails then a 404 error will have been
        sent back to the client.

        @type   netloc  : String
        @param  netloc  : Hostname or hostname:port
        @type   soc : Socket
        @param  soc : Socket on which to connect
        @return         : True if connected
        """

        i = netloc.find(':')
        if i >= 0 : host_port = netloc[:i], int(netloc[i+1:])
        else      : host_port = netloc, 80

        try :
            soc.connect(host_port)
        except socket.error, arg:
            try    : msg = arg[1]
            except : msg = arg
            self.send_error (404, msg)
            return False

        return True

    def sendStatus (self) :

        """
        Send status information.
        """

        #  Gather up the status information. Since we need to lock the status
        #  structure for the duration, do this up front to make it as quick
        #  as possible.
        #
        status = []
        statusLock.acquire()
        try    :
            for key, value in statusInfo.items() :
                status.append (string.join([ '%s=%s' % (k,v) for k, v in value.items()], ';'))
        except :
            pass
        statusLock.release()

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')
        self.connection.send  (string.join(status, '\n'))
        self.connection.send  ('\n')

    def ident (self) :

        """
        Request scraper and run identifiers, and host permissions from the UML.
        This uses local and remote port numbers to identify a TCP/IP connection
        from the scraper running under the controller.
        """

        scraperID = None
        runID     = None

        rem       = self.connection.getpeername()
        loc       = self.connection.getsockname()
        ident     = urllib.urlopen ('http://%s:9001/Ident?%s:%s' % (rem[0], rem[1], loc[1])).read()

        for line in string.split (ident, '\n') :
            key, value = string.split (line, '=')
            if key == 'runid' :
                runID     = value
                continue
            if key == 'scraperid' :
                scraperID = value
                continue
            if key == 'allow' :
                self.m_allowed.append (value)
                continue
            if key == 'block' :
                self.m_blocked.append (value)
                continue

        return scraperID, runID

    def blockmessage(self, url):
        qurl = urllib.quote(url)
        return """Scraperwiki blocked access to "%s".  Click <a href="/whitelist/?url=%s">here</a> for details.""" % (url, qurl)


    def do_CONNECT (self) :

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        scraperID, runID = self.ident ()

        self.swlog().log (scraperID, runID, 'P.CONNECT', arg1 = self.path)

        if not self.hostAllowed (self.path, scraperID, runID) :
            self.send_error (403, self.blockmessage(self.path))
            self.swlog().log (scraperID, runID, 'P.ERROR', arg1 = 'Denied',  arg2 = self.path)
            return

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self._connect_to(self.path, soc):
                self.log_request(200)
                self.wfile.write(self.protocol_version +
                                 " 200 Connection established\r\n")
                self.wfile.write("Proxy-agent: %s\r\n" % self.version_string())
                self.wfile.write("\r\n")
                self._read_write(soc)
        finally:
            soc.close()
            self.connection.close()

        self.swlog().log (scraperID, runID, 'P.DONE', arg1 = self.path)

    def retrieve (self, method) :

        """
        Handle GET and POST requests.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        isSW = netloc[-16:] == '.scraperwiki.com'

        #  Path /Status returns status information.
        #
        if path == '/Status'  :
            self.sendStatus ()
            self.connection.close()
            return

        scraperID, runID = self.ident ()
        self.swlog().log (scraperID, runID, 'P.GET', arg1 = self.path)

        if path == '' or path is None :
            path = '/'

        if scm not in [ 'http', 'https' ] or fragment or not netloc :
            self.send_error (400, "Malformed URL %s" % self.path)
            self.swlog().log (scraperID, runID, 'P.ERROR', arg1 = 'Bad URL', arg2 = self.path)
            return
        if not self.hostAllowed (self.path, scraperID, runID) :
            self.swlog().log (scraperID, runID, 'P.ERROR', arg1 = 'Denied',  arg2 = self.path)
            self.send_error (403, self.blockmessage(self.path))
            return

        if runID is not None :
            statusLock.acquire ()
            try    : statusInfo[runID] = { 'runID' : runID, 'scraperID' : scraperID, 'path' : self.path }
            except : pass
            statusLock.release ()

        ctag    = None
        used    = None
        content = None
        cache   = 0
        try    : cache = int(self.headers['x-cache'])
        except : pass

        #  Check if caching might be possible. This is the case if
        #   * Caching has been enabled
        #   * The x-cache header is greater than zero
        #
        if not isSW and useCache and cache > 0 :

            #  "cbits" will be set to a 3-element list comprising the path (including
            #  query bits), the url-encoded content if any, and the cookie string, if any.
            #
            cbits = None

            #  GET is easy, note the path, the content is empty. Cookies will be set
            #  later.
            #
            if method == "GET" :

                cbits = [ self.path, '', '' ]

            #  For POST, check that 'content-type' is 'application/x-www-form-urlencoded'
            #  and that we have a content length. If so then the content is read and
            #  noted along with the path. The content will be passed on later.
            #
            if method == "POST" \
                and 'content-length' in self.headers \
                and 'content-type'   in self.headers \
                and self.headers['content-type'] == 'application/x-www-form-urlencoded' :

                clen    = int(self.headers['content-length'])
                content = ''
                while len(content) < clen :
                    data = self.connection.recv (clen - len(content))
                    if data is None or data == '' :
                        break
                    content += data

                cbits = [ self.path, content, '' ]

            #  If we can cache then add cookies if any, and calculate a hash on
            #  the path, content and cookies. Hive off the first two digit pairs
            #  for directories (which are created if needed) and generate a
            #  path name.
            #
            if cbits is not None :

                if 'cookie' in self.headers :
                    cbits[2] = self.headers['cookie']

                ctag = hashlib.sha1(string.join (cbits, '____')).hexdigest()

        db = None
        if ctag :
            try :
                import MySQLdb
                db      = MySQLdb.connect \
                        (    host       = config.get ('httpproxy', 'dbhost'), 
                             user       = config.get ('httpproxy', 'user'  ), 
                             passwd     = config.get ('httpproxy', 'passwd'),
                             db         = config.get ('httpproxy', 'db'    ),
                             charset    = 'utf8'
                        )
            except :
                pass

        #  Try opening a possible cache file. If this succeeds then we can
        #  simply send the content as the reply. If not then we go to the real
        #  server, possibly storing results in the cacahe.
        #
        try    :
            cursor    = db.cursor()
            cursor.execute ('select id, page from httpcache where tag = %s and time_to_sec(timediff(now(), stamp)) < %s', [ ctag, cache ])
            id, page  = cursor.fetchone()
            cursor    = db.cursor()
            cursor.execute ('update httpcache set stamp = now(), hits = hits + 1 where tag = %s', [ ctag ])
            self.connection.send(page)
            used = 'CACHED'
        except :
            startat = time.strftime ('%Y-%m-%d %H:%M:%S')
            soc     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try :
                if self._connect_to (netloc, soc) :
                    self.log_request()
                    soc.send \
                        (   "%s %s %s\r\n" %
                            (   self.command,
                                urlparse.urlunparse (('', '', path, params, query, '')),
                                self.request_version
                        )   )
                    self.headers['Connection'] = 'close'
                    for key, value in self.headers.items() :
                        if key == 'Proxy-Connection' :
                            continue
                        if key == 'x-scraperid' :
                            continue
                        if key == 'x-runid'     :
                            continue
                        if key == 'x-cache'     :
                            continue
                        soc.send ('%s: %s\r\n' % (key, value))
                    if isSW :
                        soc.send ("%s: %s\r\n" % ('x-scraperid', scraperID and scraperID or ''))
                        soc.send ("%s: %s\r\n" % ('x-runid',     runID     and runID     or ''))
                    soc.send ("\r\n")
                    if content :
                        soc.send (content)
                    resp = self._read_write(soc)
                    if db :
                        cursor = db.cursor()
                        cursor.execute \
                            (   '''
                                insert  into    httpcache
                                        (       tag,
                                                url,
                                                page,
                                                hits,
                                                scraperid,
                                                runid
                                        )
                                values  ( %s, %s, %s, %s, %s, %s )
                                ''',
                                [   ctag, self.path, resp, 1, scraperID, runID    ]
                            )
            finally :
                soc  .close()
        finally :
            self.connection.close()

        if runID is not None :
            statusLock.acquire ()
            try    : del statusInfo[runID]
            except : pass
            statusLock.release ()

        self.swlog().log (scraperID, runID, 'P.DONE', arg1 = self.path, arg2 = used)

    def _read_write (self, soc, idle = 0x7ffffff) :

        """
        Copy data back and forth between the client and the server.

        @type   soc     : Socket
        @param  soc     : Socket to server
        @type   idle    : Integer
        @param  idel    : Maximum idling time between data
        @return String  : Text received from server
        """

        resp  = []
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
                        if i is soc :
                            resp.append (data)
                    else :
                        busy = False
                        break
            if count >= idle : 
                break

        return string.join (resp, '')

    def do_GET (self) :

        self.retrieve ("GET" )

    def do_POST (self) :

        self.retrieve ("POST")

#   do_HEAD   = do_GET
    do_PUT    = do_POST
#   do_DELETE = do_GET


class HTTPProxyServer \
        (   SocketServer.ThreadingMixIn,
            BaseHTTPServer.HTTPServer
        ) :
    pass


def execute (port) :

    HTTPProxyHandler.protocol_version = "HTTP/1.0"

    httpd = HTTPProxyServer(('', port), HTTPProxyHandler)
    sa    = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."

    httpd.serve_forever()


def sigTerm (signum, frame) :

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove (varDir + '/run/httpproxy.pid')
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
            varDir   = arg[ 9:]
            continue

#        if arg[:11] == '--cacheDir='  :
#            cacheDir = arg[11:]
#            continue

        if arg[ :9] == '--config='  :
            confnam  = arg[ 9:]
            continue

        if arg == '--useCache' :
            useCache = True
            continue

        if arg == '--allowAll' :
            allowAll = True
            continue

        if arg == '--subproc' :
            subproc  = True
            continue

        if arg == '--daemon' :
            daemon   = True
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
            sys.stdout = open (varDir + '/log/httpproxy', 'w', 0)
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

        pf = open (varDir + '/run/httpproxy.pid', 'w')
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

            sys.stdout.write("Forked subprocess: %d\n" % child)
            sys.stdout.flush()
    
            os.wait()

    statusLock = threading.Lock()

    config = ConfigParser.ConfigParser()
    config.readfp (open(confnam))

    execute (config.getint ('httpproxy', 'port'))
