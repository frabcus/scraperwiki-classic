#!/bin/sh -
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
import  OpenSSL
import  re

global config

USAGE       = " [--uid=#] [--gid=#] [--allowAll] [--varDir=dir] [--subproc] [--daemon] [--config=file] [--useCache] [--mode=H|S|P]"
child       = None
config      = None
varDir      = '/var'
varName     = 'webproxy'
useCache    = False
uid         = None
gid         = None
allowAll    = False
mode        = 'P'
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
        if re.match("http://127.0.0.1[/:]", path):
            allowed = True
        
        # first if it is the white-list
        for allow in self.m_allowed :
            if re.match(allow, path) :
                allowed = True
        
        # but not if it is in the black-list
        for block in self.m_blocked :
            if re.match(block, path) :
                allowed = False

        return allowed

    def _connect_to (self, scheme, netloc) :

        """
        Connect to host. If the connection fails then a 404 error will have been
        sent back to the client.

        @type   netloc  : String
        @param  netloc  : Hostname or hostname:port
        @return         : Socket
        """

        i = netloc.find(':')
        if i >= 0 : host_port = netloc[:i], int(netloc[i+1:])
        else      : host_port = netloc, scheme == 'https' and 443 or 80

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if scheme == 'https' :
            try :
                import ssl
                soc = ssl.wrap_socket(soc)
            except :
                self.send_error (404, "No ssl support, python 2.5")
                return None

        try :
            soc.connect(host_port)
        except socket.error, arg:
            try    : msg = arg[1]
            except : msg = arg
            self.send_error (404, msg)
            return None

        return soc

    def sendReply (self, reply) :

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n' )
        self.connection.send  (reply)
        self.connection.send  ('\n' )

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

        self.sendReply  (string.join(status, '\n'))

    def sendPage (self, id) :

        try :
            import MySQLdb
            db      = MySQLdb.connect \
                    (    host       = config.get (varName, 'dbhost'), 
                         user       = config.get (varName, 'user'  ), 
                         passwd     = config.get (varName, 'passwd'),
                         db         = config.get (varName, 'db'    ),
                         charset    = 'utf8'
                    )
        except :
            self.sendReply ('Cannot connect to database')
            return

        cursor = db.cursor()
        cursor.execute ('select page from httpcache where id = %s', [ id ])
        try :
            page = cursor.fetchone()[0]
        except :
            self.sendReply ('Page not found')
            return

        self.connection.sendall (page)

    def ident (self) :

        """
        Request scraper and run identifiers, and host permissions from the UML.
        This uses local and remote port numbers to identify a TCP/IP connection
        from the scraper running under the controller.
        """

        scraperID = None
        runID     = None
        cache     = 0

        rem       = self.connection.getpeername()
        loc       = self.connection.getsockname()

        #  If running as a transparent HTTP or HTTPS then the remote end is connecting
        #  to port 80 or 443 irrespective of where we think it is connecting to; for a
        #  non-transparent proxy use the actual port.
        #
        if   mode == 'H' : port = 80
        elif mode == 'S' : port = 443
        else             : port = loc[1]
        ident     = urllib.urlopen ('http://%s:9001/Ident?%s:%s' % (rem[0], rem[1], port)).read()

        for line in string.split (ident, '\n') :
            if line == '' :
                continue
            key, value = string.split (line, '=')
            if key == 'runid' :
                runID     = value
                continue
            if key == 'scraperid' :
                scraperID = value
                continue
            if key == 'allow'  :
                self.m_allowed.append (value)
                continue
            if key == 'block'  :
                self.m_blocked.append (value)
                continue
            if key == 'option' :
                name, opt = string.split (value, ':')
                if name == 'webcache' : cache = int(opt)

        return scraperID, runID, cache

    def blockmessage(self, url):

        qurl = urllib.quote(url)
        return """Scraperwiki blocked access to "%s".""" % (qurl)


    def do_CONNECT (self) :

        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        scraperID, runID, cache = self.ident ()

        self.swlog().log (scraperID, runID, 'P.CONNECT', arg1 = self.path)

        if not self.hostAllowed (self.path, scraperID, runID) :
            self.send_error (403, self.blockmessage(self.path))
            self.swlog().log (scraperID, runID, 'P.ERROR', arg1 = 'Denied',  arg2 = self.path)
            return

        try:
            soc = self._connect_to(scheme, netloc)
            if soc is not None :
                self.log_request(200)
                self.connection.send(self.protocol_version +
                                 " 200 Connection established\r\n")
                self.connection.send("Proxy-agent: %s\r\n" % self.version_string())
                self.connection.send("\r\n")
                self.connection.send(self.getResponse(soc))
        finally:
            if soc is not None :
                soc.close()
            self.connection.close()

        self.swlog().log (scraperID, runID, 'P.DONE', arg1 = self.path)

    def notify (self, host, **query) :

        query['message_type'] = 'sources'
        try    : urllib.urlopen ('http://%s:9001/Notify?%s'% (host, urllib.urlencode(query))).read()
        except : pass

    def bodyOffset (self, page) :

        try    : offset1 = string.index (page, '\r\n\r\n')
        except : offset1 = 0x3fffffff
        try    : offset2 = string.index (page, '\n\n'    )
        except : offset2 = 0x3fffffff

        if offset1 < offset2 : return offset1 + 4
        return offset2 + 2

    def fetchedDiffers (self, fetched, cached) :

        if cached is not None :
            fbo = self.bodyOffset (fetched[1])
            cbo = self.bodyOffset (cached [1])
            return fetched[1][fbo:] != cached[1][cbo:]

        return True

    def retrieve (self, method) :

        """
        Handle GET and POST requests.
        """

        #  If this is a transparent HTTP or HTTPS proxy then modify the path with the
        #  protocol and the host.
        #
        if   mode == 'H' : self.path = 'http://%s%s'  % (self.headers['host'], self.path)
        elif mode == 'S' : self.path = 'https://%s%s' % (self.headers['host'], self.path)

        #  This ensures that we only add headers into requests that are going into the scraperwiki
        #  system (or a runlocal sw system)
        #
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        isSW = netloc.endswith('scraperwiki.com')
        if netloc[:9] == '127.0.0.1':
            isSW = True

        #  Path /Status returns status information.
        #
        if path == '/Status'  :
            self.sendStatus ()
            self.connection.close()
            return

        if path == '/Page' :
            self.sendPage   (query)
            self.connection.close()
            return            

        scraperID, runID, cacheFor = self.ident ()
        self.swlog().log (scraperID, runID, 'P.GET', arg1 = self.path)

        if path == '' or path is None :
            path = '/'

        if scheme not in [ 'http', 'https' ] or fragment or not netloc :
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
        content = None
        bytes   = 0
        cached  = None
        fetched = None

        #  Generate a hash on the request unless this is a request for a scraperwiki.com
        #  page
        #
        if not isSW :
            #
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
            #  the path, content and cookies.
            #
            if cbits is not None :

                if 'cookie' in self.headers :
                    cbits[2] = self.headers['cookie']

                ctag = hashlib.sha1(string.join (cbits, '____')).hexdigest()

        #  If we have a cache tag then connect to the database. If this fails
        #  then continue without it so the system continues to work in a
        #  degraded way.
        #
        db = None
        if ctag is not None :
            try :
                import MySQLdb
                db      = MySQLdb.connect \
                        (    host       = config.get (varName, 'dbhost'), 
                             user       = config.get (varName, 'user'  ), 
                             passwd     = config.get (varName, 'passwd'),
                             db         = config.get (varName, 'db'    ),
                             charset    = 'utf8'
                        )
            except :
                pass

        #  See if the page can be retrieved from the database. If so then
        #  update the last-accessed stamp to now and increment the hit count.
        #
        if db is not None :
            cursor    = db.cursor()
            cursor.execute \
                (   '''
                    select  id,
                            page,
                            time_to_sec(timediff(now(), stamp))
                    from    httpcache
                    where   tag = %s
                    and     substr(page,1,6) = 'HTTP/1'
                    order   by id desc
                    limit   1
                    ''',
                    [ ctag ]  #, cacheFor ]
                )
##                   and     time_to_sec(timediff(now(), stamp)) < %s
            cached  = cursor.fetchone()
            if cached is not None :
                cursor  = db.cursor()
                cursor.execute ('update httpcache set stamp = now(), hits = hits + 1 where id = %s', [ cached[0] ])

        #  Actually fetch the page if:
        #   * There is no cache tag
        #   * Not using the cache
        #   * Cache timeout is set to zero
        #   * Page was not in the cache anyway
        #   * Cached page is too old
        #
        if ctag is None or not useCache or cacheFor <= 0 or cached is None or cached[2] > cacheFor :

            startat = time.strftime ('%Y-%m-%d %H:%M:%S')
            try :
                soc = self._connect_to (scheme, netloc)
                if soc is not None :
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
                    fetched  = [ None, self.getResponse(soc), 0 ]
                    if db :
                        if self.fetchedDiffers (fetched, cached) :
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
                                    [   ctag, self.path, fetched[1], 1, scraperID, runID    ]
                                )
                            def iid (cursor) :
                                try    : return cursor.lastrowid
                                except : pass
                                try    : return cursor.insert_id()
                                except : pass
                                return None
                            fetched[0] = iid(cursor)
                        else :
                            fetched[0] = cached[0]

            finally :
                if soc is not None :
                    soc.close()

        if   fetched is not None : cacheid, page, age = fetched
        elif cached  is not None : cacheid, page, age = cached
        else                     : cacheid, page, age = '', ''

        if cacheid is None       : cacheid = ''

        bodyat  = self.bodyOffset (page)
        headers = page[:bodyat]
        bytes   = len(page) - bodyat
        if bytes < 0 :
            bytes = len(page)

        mimetype = ''
        for line in headers.split('\n') :
            if line.find(':') > 0 :
                name, value = line.split(':', 1)
                if name.lower() == 'content-type' :
                    if value.find(';') :
                        value, rest = value.split(';',1)
                        mimetype = value.strip()

        failedmessage = ''
        m = re.match ('^HTTP/1\\..\\s+([0-9]+)\\s+(.*?)[\r\n]', page)
        if m :
            if m.group(1) != '200' :
                failedmessage = 'Failed:' + m.group(1) + "  " + m.group(2)
        else :
            failedmessage = 'Failed: (code missing)'

        self.notify \
            (   self.connection.getpeername()[0],
                runid           = runID,
                scraperid       = scraperID,
                url             = self.path,
                failedmessage   = failedmessage,
                bytes           = bytes,
                mimetype        = mimetype,
                cacheid         = cacheid,
                last_cacheid    = cached  is not None and cached[0] or '',
                cached          = cached  is not None
            )

        self.connection.sendall (page)
        self.connection.close()

        if runID is not None :
            statusLock.acquire ()
            try    : del statusInfo[runID]
            except : pass
            statusLock.release ()

        self.swlog().log (scraperID, runID, 'P.DONE', arg1 = self.path, arg2 = cacheid)

    def getResponse (self, soc, idle = 0x7ffffff) :

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
                    try    : data = i.recv (8192)
                    except : return
                    if data is not None and data != '' :
                        count = 0
                        if i is soc : resp.append (data)
                        else        : soc .send  (data)
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

class HTTPSProxyHandler (HTTPProxyHandler) :

    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

class HTTPProxyServer \
        (   SocketServer.ThreadingMixIn,
            BaseHTTPServer.HTTPServer
        ) :
    pass


class HTTPSProxyServer (HTTPProxyServer) :

    def __init__(self, server_address, HandlerClass):

        HTTPProxyServer.__init__(self, server_address, HandlerClass)
        ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
        fpem = '/var/www/scraperwiki/uml/httpproxy/server.pem'
        ctx.use_privatekey_file (fpem)
        ctx.use_certificate_file(fpem)
        self.socket = OpenSSL.SSL.Connection \
                            (   ctx,
                                socket.socket(self.address_family, self.socket_type)
                            )
        self.server_bind    ()
        self.server_activate()


def execute () :

    HTTPProxyHandler.protocol_version  = "HTTP/1.0"
    HTTPSProxyHandler.protocol_version = "HTTPS/1.0"

    port = config.getint (varName, 'port')

    if mode == 'S' :
           httpd = HTTPSProxyServer (('', port), HTTPSProxyHandler)
    else : httpd = HTTPProxyServer  (('', port), HTTPProxyHandler )

    sa    = httpd.socket.getsockname()
    print "Serving on", sa[0], "port", sa[1], "..."

    httpd.serve_forever()


def sigTerm (signum, frame) :

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove ('%s/run/%s.pid' % (varDir, varName))
    except : pass
    sys.exit (1)


if __name__ == '__main__' :

    subproc = False
    daemon  = False
    confnam = 'uml.cfg'

    for arg in sys.argv[1:] :

        if arg in ('-h', '--help')  :
            print "usage: " + sys.argv[0] + USAGE
            sys.exit (1)

        if arg[: 6] == '--uid='     :
            uid      = arg[ 6:]
            continue

        if arg[: 6] == '--gid='     :
            gid      = arg[ 6:]
            continue

        if arg[ :9] == '--varDir='  :
            varDir   = arg[ 9:]
            continue

        if arg[ :9] == '--config='  :
            confnam  = arg[ 9:]
            continue

        if arg[: 7] == '--mode='    :
            mode     = arg[ 7:]
            continue

        if arg == '--useCache'      :
            useCache = True
            continue

        if arg == '--allowAll'      :
            allowAll = True
            continue

        if arg == '--subproc'       :
            subproc  = True
            continue

        if arg == '--daemon'        :
            daemon   = True
            continue

        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)


    if mode not in [ 'H', 'S', 'P' ] :
        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)

    if   mode == 'H' : varName = 'httpproxy'
    elif mode == 'S' : varName = 'httpsproxy'

    #  If executing in daemon mode then fork and detatch from the
    #  controlling terminal. Basically this is the fork-setsid-fork
    #  sequence.
    #
    if daemon :

        if os.fork() == 0 :
            os .setsid()
            sys.stdin  = open ('/dev/null')
            sys.stdout = open ('%s/log/%s' % (varDir, varName), 'w', 0)
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

        pf = open ('%s/run/%s.pid' % (varDir, varName), 'w')
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

    execute ()
