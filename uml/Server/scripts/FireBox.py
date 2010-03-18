#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

__doc__ = """ScraperWiki FireBox

Hacked by.                                      Mike Richardson
"""

__version__ = "ScraperWiki_0.0.1"

import BaseHTTPServer
import SocketServer

import urlparse
import cgi
import os
import sys
import time
import signal
import string
import FireStarter

USAGE      = " [--port=port] [--varDir=dir] [--subproc] [--daemon]"
child      = None
port       = 9004
varDir	   = '/var'

class ScraperFireBox (BaseHTTPServer.BaseHTTPRequestHandler) :

    """
    FireBox base class. This is derived from a base HTTP
    server class, and contains code to process and dispatch
    requests.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "FireBox/" + __version__
    rbufsize       = 0

    def __init__ (self, *alist, **adict) :

        """
        Class constructor. All arguments (positional and keyed) are passed down to
        the base class constructor.
        """

        self.m_cgi_fp       = None
        self.m_cgi_headers  = None
        self.m_cgi_env      = None
        self.m_fs           = None

        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

    def storeEnvironment (self, rfile, headers, method, query) :

        """
        Store envronment information needed to retrieve CGI parameters.

        @type   rfile   : Stream
        @param  rfile   : Incoming stream from client
        @type   headers : Dictionary
        @param  headers : HTTP headers dictionary if needed
        @type   method  : String
        @param  method  : HTTP request method
        @type   query   : String
        @param  query   : HTTP query string
        """
        self.m_cgi_fp       = rfile
        self.m_cgi_headers  = headers
        self.m_cgi_env      = { 'REQUEST_METHOD' : method }

        if query                            : self.m_cgi_env['QUERY_STRING'  ] = query
        if 'content-type'   in self.headers : self.m_cgi_env['CONTENT_TYPE'  ] = self.headers['content-type'  ]
        if 'content-length' in self.headers : self.m_cgi_env['CONTENT_LENGTH'] = self.headers['content-length']

    def execute (self) :

        """
        Execute request. The \em path string has the leading / removed
        and is then split on the / character. The first part is used
        as the method name with \em fn prefixed. The entire split list
        is passed to the method call.

        @type   path    : String
        @param  path    : CGI execution path
        """

        fs   = cgi.FieldStorage \
                        (       fp      = self.m_cgi_fp,
                                headers = self.m_cgi_headers,
                                environ = self.m_cgi_env,
                                keep_blank_values = True
                        )
        fb   = FireStarter.FireStarter()
        fb.addPaths ('/a', '/b')
        code = fs['code'].value
        code = string.strip   (code)
        code = string.replace (code, '\r', '')
        res  = fb.execute (code, True)


        self.wfile.write ('HTTP/1.0 200 OK\n')
        self.wfile.write ('Connection: Close\n')
        self.wfile.write ('Pragma: no-cache\n')
        self.wfile.write ('Cache-Control: no-cache\n')
        self.wfile.write ('Content-Type: text/html\n')
        self.wfile.write ('\n')

        if res is None :
            self.wfile.write ('<html><body><b>')
            self.wfile.write (fb.error())
            self.wfile.write ('</b></body></html>')
            self.wfile.flush ()
            return

        self.wfile.write ('<html><body><pre>')
        self.wfile.flush ()

        try :
            line  = res.readline()
            while line is not None and line != '' :
                self.wfile.write (line)
                self.wfile.flush ()
                line  = res.readline()
        except FireStarter.FireError, e :
            self.wfile.write (str(e))
            self.wfile.flush ()

        self.wfile.write ('</pre></body></html>')
        self.wfile.flush ()

    def do_POST (self) :

        """
        Handle POST request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        self.storeEnvironment (self.rfile, self.headers, 'POST', None)
        self.execute ()

    def do_GET (self) :

        """
        Handle GET request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        self.storeEnvironment (None, None, 'GET', query)
        self.execute ()



class ThreadingHTTPServer \
        (   SocketServer.ForkingMixIn,
            BaseHTTPServer.HTTPServer
        ) :

    """
    Wrapper class providing a forking server. Note that we runn forking
    and not threaded as we may want to change the user and group id of
    the executed scripts.
    """

    pass


def execute (port) :

    """
    Execute FireBox

    @type   port    : Integer
    @param  port    : Port on which to listen
    """
    ScraperFireBox.protocol_version = "HTTP/1.0"

    httpd = ThreadingHTTPServer(('', port), ScraperFireBox)
    sa    = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."

    httpd.serve_forever()


def sigTerm (signum, frame) :

    """
    Handler for SIGTERM. Kills any child process and removes any PID
    file.

    @type   signum  : Integer
    @param  signum  : Signal number, should be SIGTERM
    @type   frame   : Python frame
    @param  frame   ; Python frame in which signal caught
    """

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove (varDir + '/run/firebox.pid')
    except : pass
    sys.exit (1)


if __name__ == '__main__' :

    subproc = False
    daemon  = False

    for arg in sys.argv[1:] :

        if arg in ('-h', '--help') :
            print "usage: " + sys.argv[0] + USAGE
            sys.exit (1)

        if arg[:7] == '--port=' :
            port = int(arg[7:])
            continue

        if arg[ :9] == '--varDir='  :
            varDir  = arg[ 9:]
            continue

        if arg == '--subproc' :
            subproc = True
            continue

        if arg == '--daemon' :
            daemon = True
            continue

        if arg == '--nofirewall' :
            firewall = False
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
            sys.stdout = open (varDir + '/log/firebox', 'w')
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

        pf = open (varDir + '/run/firebox.pid', 'w')
        pf.write  ('%d\n' % os.getpid())
        pf.close  ()

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

    execute (port)
