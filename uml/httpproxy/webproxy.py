#!/bin/sh -
"exec" "python" "-O" "$0" "$@"


import BaseHTTPServer
import SocketServer
import select
import socket
import urlparse
import signal
import os
import sys
import time
import threading
import string 
import urllib
import urllib2
import ConfigParser
import optparse
import logging, logging.config
import hashlib
import OpenSSL
import re
import memcache
import grp, pwd

parser = optparse.OptionParser()
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--setuid", action="store_true")
parser.add_option("--allowAll", action="store_true")
parser.add_option("--useCache", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

logging.config.fileConfig(poptions.config)
logger = logging.getLogger('proxy')

stdoutlog = None
stdoutlog = open('/var/www/scraperwiki/uml/var/log/proxy.log'+"-stdout", 'a', 0)

cache_hosts = config.get('webproxy', 'cache')
if cache_hosts:
    cache_client = memcache.Client(cache_hosts.split(','))
else:
    cache_client = None

child       = None

mode        = 'P'   # this can be H or S for http transparent proxy cases
statusInfo  = {}

class HTTPProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler) :
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "HTTPProxy/ScraperWiki_0.0.1"
    rbufsize       = 0

    def __init__ (self, *alist, **adict) :
        self.m_allowed = []
        self.m_blocked = []
        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

    def hostAllowed (self, path, scraperID) :
        if poptions.allowAll:
            return True

        # XXX Workaround - if ident failed then allow by default
        if not scraperID:
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
        print "hihih"
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
        self.sendReply("some status here")

    def sendPage (self, id) :
        """
        Retreive page from cache if possible
        """
        # TODO: Add better handling for the page not being found in the cache
        if not id:
            logger.warning('No ID argument passed to sendPage()')
            return 

        page = cache_client.get(id)
        if not page:
            logger.warning('Page not found in cache')
            self.sendReply ('Page not found in cache')
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
        if mode == 'H':
            port = 80
        elif mode == 'S':
            port = 443
        else:
            port = loc[1]

        for attempt in range(5):
            try:
                ident = urllib2.urlopen('http://%s:9001/Ident?%s:%s' % (rem[0], rem[1], port)).read()
                if ident.strip() != "":
                    break
            except:
                pass

        for line in string.split (ident, '\n'):
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
        print self.path, "ppp"
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        scraperID, runID, cache = self.ident ()


        if not self.hostAllowed (self.path, scraperID) :
            self.send_error (403, self.blockmessage(self.path))
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
        if cached is None:
            return True
        else:
            fbo = self.bodyOffset(fetched)
            cbo = self.bodyOffset(cached)
            return fetched[fbo:] != cached[cbo:]

    def do_GET (self) :
        self.retrieve ("GET" )

    def do_POST (self) :
        self.retrieve ("POST")


    def retrieve (self, method):
        logger.info([method, self.path])
        #  If this is a transparent HTTP or HTTPS proxy then modify the path with the
        #  protocol and the host.
        if mode == 'H':
            self.path = 'http://%s%s'  % (self.headers['host'], self.path)
        elif mode == 'S':
            self.path = 'https://%s%s' % (self.headers['host'], self.path)

        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        isSW = netloc.startswith('127.0.0.1') or netloc.endswith('scraperwiki.com')
        
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
        if path == '' or path is None :
            path = '/'

        if scheme not in [ 'http', 'https' ] or fragment or not netloc :
            self.send_error (400, "Malformed URL %s" % self.path)
            return
        if not self.hostAllowed (self.path, scraperID) :
            self.send_error (403, self.blockmessage(self.path))
            return

        ctag     = None
        content  = None
        bytes    = 0
        cached   = None
        fetched  = None
        ddiffers = False

        #  Generate a hash on the request ...
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

        if ctag and cache_client and poptions.useCache:
            cached = cache_client.get(ctag)
        else:
            cached = None

        #  Actually fetch the page if:
        #   * There is no cache tag
        #   * Not using the cache
        #   * Cache timeout is set to zero
        #   * Page was not in the cache anyway
        #
        if isSW or cacheFor <= 0 or cached is None:

            startat = time.strftime ('%Y-%m-%d %H:%M:%S')
            soc = None
            try :
                soc = self._connect_to (scheme, netloc)
                if soc is not None:
                    req = "%s %s %s\r\n" % (self.command, urlparse.urlunparse (('', '', path, params, query, '')), self.request_version)
                    logger.debug(req)
                    soc.send(req)
                    self.headers['Connection'] = 'close'
                    for key, value in self.headers.items() :
                        if key != 'Proxy-Connection' :
                            soc.send ('%s: %s\r\n' % (key, value))
                    soc.send ("\r\n")
                    if content:
                        soc.send(content)

                    fetched = self.getResponse(soc)

                    if ctag and cache_client:
                        if self.fetchedDiffers(fetched, cached):
                            cache_client.set(ctag, fetched)

            finally :
                if soc is not None :
                    soc.close()

        if fetched: 
            cacheid, page = ctag, fetched
        elif cached:
            cacheid, page = ctag, cached
        else:
            cacheid, page = '', ''

        if cacheid is None:
            cacheid = ''

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
                    if value.find(';') > 0 :
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
                last_cacheid    = cached is not None or '',
                cached          = cached is not None,
                ddiffers        = ddiffers
            )

        self.connection.sendall (page)
        self.connection.close()



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




def sigTerm(signum, frame):
    os.kill(child, signal.SIGTERM)
    try:
        os.remove(poptions.pidfile)
    except OSError:
        pass  # no such file
    sys.exit(1)


if __name__ == '__main__' :
    # daemon
    if os.fork() == 0 :
        os .setsid()
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

    # subproc
    signal.signal(signal.SIGTERM, sigTerm)
    while True:
        child = os.fork()
        if child == 0 :
            break
        logger.info("Forked subprocess: %d" % child)
        os.wait()
        logger.warning("Forked subprocess ended: %d" % child)


    HTTPProxyHandler.protocol_version  = "HTTP/1.0"
        #HTTPSProxyHandler.protocol_version = "HTTPS/1.0"
        # may need 3 threads to handle HTTPS and FTP cases
    port = config.getint ("webproxy", 'port')
    httpd = HTTPProxyServer(('', port), HTTPProxyHandler)

    sa = httpd.socket.getsockname()
    logger.info("Serving on %s port %s ..." % (sa[0], sa[1]))

    httpd.serve_forever()
