#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

__doc__ = """ScraperWiki Controller

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
import socket
import string
import StringIO
import resource
import subprocess
import re
import cgi
import ConfigParser

try    : import json
except : import simplejson as json

global config
global firewall

USAGE      = " [--varDir=dir] [--addPath=path] [--subproc] [--daemon] [--firewall=option] [--config=file] [--name=name]"
child      = None
varDir	   = '/var'
config	   = None
name	   = None
firewall   = None
re_resolv  = re.compile ('nameserver\s+([0-9.]+)')


def firewallBegin (rules) :

    """
    Append initial firewall (iptables) rules. These allow traffic to
    the host (both the host's own address and and the tap address),
    to the DataProxy, and to the logging database. Also add a rule for
    each nameserver.
    """

    rules.append ('*filter')
    rules.append ('-A OUTPUT -p tcp -d %s -j ACCEPT'              % (config.get (socket.gethostname(), 'host')))
    rules.append ('-A OUTPUT -p tcp -d %s -j ACCEPT'              % (config.get (socket.gethostname(), 'tap' )))
    rules.append ('-A OUTPUT -p tcp -d %s --dport %s -j ACCEPT'   % (config.get ('dataproxy', 'host'), config.get ('dataproxy', 'port')))
    rules.append ('-A OUTPUT -p tcp -d %s --dport 3306 -j ACCEPT' % (config.get ('dataproxy', 'host')))
    for line in open ('/etc/resolv.conf').readlines() :
        m = re_resolv.match (line)
        if m :
            rules.append ('-A OUTPUT -p udp -d %s --dport 53 -j ACCEPT' % m.group(1))


def firewallEnd (rules) :

    """
    Append final filewall (iptables) rules. These reject anything
    not explicitely allowed, then commit.
    """

    rules.append ('-A OUTPUT -j REJECT')
    rules.append ('COMMIT')


def firewallSetup (rules, stdout, stderr) :

    """
    Set up firewall rules. The actual setup is skipped unless we are
    running as root, so that the controller can be run outside of a
    UML instance.
    """

    rname = '/tmp/iptables.%s' % os.getpid()
    rfile = open (rname, 'w')
    rfile.write  (string.join (rules, '\n') + '\n')
    rfile.close  ()

    if os.getuid() == 0 :

        p = subprocess.Popen \
                (    'iptables-restore < %s' % rname,
                     shell	= True,
                     stdin	= open('/dev/null'),
                     stdout	= stdout,
                     stderr	= stderr
		)
        p.wait ()

    os.remove   (rname)


class TaggedStream :

    """
    This class is duck-type equivalent to a file object. Used to replace
    sys.stdout and sys.stderr, to insert a <scraperwiki:message> before
    each chunck of output.
    """

    def __init__ (self, fd) :

        """
        Constructor. The file descriptor is saved and a local buffer
        initialised to an empty string.
        """

        self.m_fd   = fd
        self.m_text = ''

    def write (self, text) :

        """
        Write the specified text. This is appened to the local buffer,
        which is then flushed if it contains a newline.
        """

        self.m_text += text
        if self.m_text.find ('\n') >= 0 :
            self.flush ()

    def flush (self) :

        """
        Flush buffered text independent of the presence of newlines.
        """

        #  Skip ready prefixes lines. Hack until there is an API to
        #  generate data and sources message. 
        #
        if self.m_text.startswith ('<scraperwiki:message') :
            self.m_fd.write (self.m_text)
            self.m_text = ''
            return

        if self.m_text != '' :
            msg  = { 'message_type' : 'console', 'content' : self.m_text[:100] }
            if len(self.m_text) >= 100 :
                msg['content_long'] = self.m_text
            self.m_fd.write ('<scraperwiki:message type="console">' + json.dumps(msg) + '\n')
            self.m_fd.flush ()
            self.m_text = ''

    def close (self) :

        self.m_fd.close ()

    def fileno (self) :

        return self.m_fd.fileno ()


class BaseController (BaseHTTPServer.BaseHTTPRequestHandler) :

    """
    Controller base class. This is derived from a base HTTP
    server class, and contains code to process and dispatch
    requests.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "Controller/" + __version__
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
        self.m_stdout	    = sys.stdout
        self.m_stderr	    = sys.stderr

        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)

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

    def storeEnvironment (self, rfile, headers, method, query) :

        """
        Store envronment information needed to retrieve CGI parameters. The
        information is stored rather than used immediately as it will also
        be used when executing a script in CGI mode. The \em rfile and \em headers
        arguments may be \em None if not needed (for a \em GET request).

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

    def getFieldStorage (self) :

        """
        Get a CGI field storage object. This is created once on demand from
        the stored environment.

        @return         : cgi.FieldStorage instance
        """

        if self.m_fs is None :
            self.m_fs = cgi.FieldStorage \
                        (       fp      = self.m_cgi_fp,
                                headers = self.m_cgi_headers,
                                environ = self.m_cgi_env,
                                keep_blank_values = True
                        )
        return self.m_fs

    def setUser (self) :

        """
        If the \em x-setuser header is present then set that as the real and
        effective user.
        """

        if 'x-setuser'  in self.headers :
            import pwd
            try    :
                user  = pwd.getpwnam (self.headers['x-setuser' ])
                os.setreuid (user.pw_uid, user.pw_uid)
            except :
                self.send_error (404, 'User %s not found'  % self.headers['x-setuser' ])
                return

    def setGroup (self) :

        """
        If the \em x-setgroup header is present then set that as the real and
        effective group.
        """

        if 'x-setgroup' in self.headers :
            import grp
            try    :
                group = grp.getgrnam (self.headers['x-setgroup'])
                os.setregid (group.gr_gid, group.gr_gid)
            except :
                self.send_error (404, 'Group %s not found' % self.headers['x-setgroup'])
                return

    def setScraperID (self) :

        """
        If the \em x-scraperid header is present then set that as the scraper ID.
        """

        if 'x-scraperid'  in self.headers :
            os.environ['SCRAPER_GUID'] = self.headers['x-scraperid']

    def setRunID (self) :

        """
        If the \em x-runid header is present then set that as the run ID.
        """

        if 'x-scraperid'  in self.headers :
            os.environ['RUNID'] = self.headers['x-runid']

    def setRLimit (self) :

        """
        Set resource limits. Scans headers for headers starting 'x-setrlimit'.
        The header should contain three comma-separated numbers, which are
	respectively the limit code, the soft limit and the hard limit.
        """

        for name, value in self.headers.items() :
            if name[:12] == 'x-setrlimit-' :
                args = string.split (value, ',')
                resource.setrlimit (int(name[12:]), (int(args[0]), int(args[1])))

    def setIPTables (self) :

        """
        Set up IPTables firewalling. The firewall rules, as \em iptables command
        arguments, are passed as headers starting 'x-iptables-'. These are written
        to a temporary file which is used as input to the \em iptables-restore
        command.
        """

        if os.getuid() != 0 :
            return
        if 'x-noiptables' in self.headers :
            return
        if firewall != 'request' :
            return

        rules = []
        firewallBegin (rules)
        for name, value in self.headers.items() :
            if name[:11] == 'x-iptables-' :
                rfile.write (value + '\n')
        firewallEnd   (rules)
        firewallSetup (rules, self.wfile. self.wfile)

    def addPaths (self) :

        """
        Add directories to the python search path.
        command.
        """

        for name, value in self.headers.items() :
            if name[:8] == 'x-paths-' :
                sys.path.append (value)

    def addEnvironment (self) :

        """
        Add directories to the python search path.
        command.
        """

        for name, value in self.headers.items() :
            if name[:9] == 'x-setenv-' :
                bits = string.split (value, '=')
                os.environ[bits[0]] = bits[1]

    def traceback (self) :

        """
        Get the traceback mode, defaults to I{text}

        @rtype		: String
        @return		: Traceback mode
        """

        for name, value in self.headers.items() :
            if name == 'x-traceback' :
                return value
        return 'text'

    def sendIdent (self, query) :

        """
        Send ident information, specifically the scraper and run identifiers for a
        specified connection to the proxy.

        @type	query	: String
        @param	query	: (remote:local) ports from the proxy's viewpoint
        """

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')

        #  The query contains the proxy's remote port (which is the local port here)
        #  and the proxy's local port (which is the remote port here). Scan all open
        #  files for a TCP/IP stream with these two ports. If found then extract the
        #  process number; this is used to open the /tmp/ident.PID file which contains
        #  the scraper and run identifiers.
        #
	(lport, rport) = string.split (query, ':')
	p = re.compile ('python *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
        lsof = subprocess.Popen([ 'lsof', '-n', '-P' ], stdout = subprocess.PIPE).communicate()[0]
	for line in lsof.split('\n') :
	    m = p.match (line)
            if m :
                self.log_request('Ident', '(%s,%s) is pid %s' % (lport, rport, m.group(1)))
                try    : self.connection.send (open('/tmp/ident.%s' % m.group(1)).read())
                except : self.log_request('Ident', '(%s,%s) send failed' % (lport, rport))
                return
        self.log_request('Ident', '(%s,%s) not found' % (lport, rport))

    def execute (self, path) :

        """
        Execute request. The \em path string has the leading / removed
        and is then split on the / character. The first part is used
        as the method name with \em fn prefixed. The entire split list
        is passed to the method call.

        @type   path    : String
        @param  path    : CGI execution path
        """

        path = path[1:].split('/')
        try :
            method = getattr (self, "fn" + path[0])
        except :
            self.send_error (404, 'Action %s not found' % path[0])
            return

        self.log_request('Execute', path)
        method (path)

    def do_POST (self) :

        """
        Handle POST request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')
        self.storeEnvironment (self.rfile, self.headers, 'POST', None)
        self.execute          (path)

    def do_GET (self) :

        """
        Handle POST request.
        """

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')

        if path == '/Ident' :
            self.sendIdent (query)
            self.connection.close()
            return

        self.storeEnvironment (None, None, 'GET', query)
        self.execute          (path)

    def getTraceback (self, code) :

        """
        Get traceback information. Returns exception, traceback, the
        scraper file in whch the error occured and the line number.

        @return         : (exception, traceback, file, line)
        """

        if self.traceback() == 'text' :
            import backtrace
            return backtrace.backtrace ('text', code, context = 10)
        if self.traceback() == 'html' :
            import backtrace
            return backtrace.backtrace ('html', code, context = 10)

        import traceback
        tb = [ \
                string.replace (t, 'File "<string>"', 'Scraper')
                for t in traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
                if string.find (t, 'Controller.py') < 0
              ]
        return str(sys.exc_type), string.join(tb, ''), None, None

    def execPython (self, code) :

        """
        Execute a python script, passed as the text of the script. If the
        script throws an exception then generate a traceback, preceeded
        by a delimiter.
        """

        try    : scraperID  = self.headers['x-scraperid' ]
        except : scraperID  = None
        try    : runID      = self.headers['x-runid'     ]
        except : runID      = ''

        import swlogger
        swl = swlogger.SWLogger(config)
        swl.connect ()
        swl.log     (scraperID, runID, 'C.START')

        tap      = config.get (socket.gethostname(), 'tap')
        httpport = config.get ('httpproxy', 'port')
        ftpport  = config.get ('ftpproxy',  'port')

#       os.environ['http_proxy' ] = 'http://%s:%s' % (tap, port)
#       os.environ['https_proxy'] = 'http://%s:%s' % (tap, port)

        import urllib2
        import scraperwiki.utils
        HTTPProxy   = urllib2.ProxyHandler ({'http':  'http://%s:%s' % (tap, httpport)})
        HTTPSProxy  = urllib2.ProxyHandler ({'https': 'http://%s:%s' % (tap, httpport)})
        FTPProxy    = urllib2.ProxyHandler ({'ftp':   'ftp://%s:%s'  % (tap, ftpport )})
        scraperwiki.utils.setupHandlers (HTTPProxy, HTTPSProxy, FTPProxy)

        idents = []
        if scraperID is not None : idents.append ('scraperid=%s' % scraperID)
        if runID     is not None : idents.append ('runid=%s'     % runID    )
        for name, value in self.headers.items() :
            if name[:17] == 'x-addallowedsite-' :
                idents.append ('allow=%s' % value)
                continue
            if name[:17] == 'x-addblockedsite-' :
                idents.append ('block=%s' % value)
                continue

        open ('/tmp/ident.%d' % os.getpid(), 'w').write(string.join(idents, '\n'))

        try    : open ('/tmp/scraper.%d' % os.getpid(), 'w').write(code)
        except : pass

        #  Pass the configuration to the datastore. At this stage no connection
        #  is made; a connection will be made on demand if the scraper tries
        #  to save anything.
        #
        from   scraperwiki import datastore
        datastore.DataStore (config)

        #  Stdout and stderr are replaced by TaggedStream objects which
        #  tags output with <scraperwiki:message type="console">. By
        #  experiment this works with print as well as sys.stdout.write().
        #
        sys.stdout = TaggedStream (self.wfile)
        sys.stderr = TaggedStream (self.wfile)

        #  Set up a CPU time limit handler which simply throws a python
        #  exception.
        #
        def sigXCPU (signum, frame) :
            raise Exception ("CPUTimeExceeded")

        signal.signal (signal.SIGXCPU, sigXCPU)

        try :
            import imp
            ostimes1   = os.times ()
            cltime1    = time.time()
            mod        = imp.new_module ('scraper')
            exec code in mod.__dict__
            ostimes2   = os.times ()
            cltime2    = time.time()
            try    :
                sys.stdout.write \
			(	'%d seconds elapsed, used %d CPU seconds' % 
				(	int(cltime2 - cltime1),
					int(ostimes2[0] - ostimes1[0])
			)	)
            except :
                pass
            etext, trace, infile, atline = None, None, None, None
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = self.wfile
            sys.stderr = self.wfile
            swl.log     (scraperID, runID, 'C.END',   arg1 = ostimes2[0] - ostimes1[0], arg2 = ostimes2[1] - ostimes1[1])
        except Exception, e :
            import errormapper
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = self.wfile
            sys.stderr = self.wfile
            emsg = errormapper.mapException (e)
            etext, trace, infile, atline = self.getTraceback (code)
            sys.stdout.write \
		(   '<scraperwiki:message type="exception">%s\n' % \
                    json.dumps \
                    (	{	'content'	: emsg,
                          	'content_long'	: trace,
			  	'filename'	: infile,
			  	'lineno'	: atline
			}
                )   )
            sys.stdout.flush ()
            swl.log     (scraperID, runID, 'C.ERROR', arg1 = etext, arg2 = trace)

#        try    : os.remove ('/tmp/scraper.%d' % os.getpid())
#        except : pass
#        try    : os.remove ('/tmp/ident.%d'   % os.getpid())
#        except : pass

class ScraperController (BaseController) :

    """
    Class derived from \em BaseController to implement scraper functionality.
    The methods named \em fnName are the execution methods.
    """

    def fnCommand (self, path) :

        fs      = self.getFieldStorage ()
        command = fs['command'].value

        #  Apply resource limits, and set group and user.
        #
        self.setIPTables    ()
        self.setRLimit      ()
        self.setGroup       ()
        self.setUser        ()
        self.addPaths       ()
        self.addEnvironment ()
        self.setScraperID   ()
        self.setRunID       ()

        p = subprocess.Popen \
		(	command,
			shell	= True,
			stdin	= open('/dev/null'),
			stdout	= self.wfile,
			stderr	= self.wfile
		)
	p.wait ()

    def fnExecute (self, path) :

        """
        Execute python code passed as a file attached as the \em script
        parameter directly. This should be used for control functions
        so no resource limits are applied, and the code is run as the
        current user.

        @type   path    : List
        @param  path    : Split CGI execution path
        """

        fs = self.getFieldStorage ()

        sys.stdin  = self.rfile
        sys.stdout = self.wfile

        #  Apply resource limits, and set group and user.
        #
        self.setIPTables    ()
        self.setRLimit      ()
        self.setGroup       ()
        self.setUser        ()
        self.addPaths       ()
        self.addEnvironment ()
        self.setScraperID   ()
        self.setRunID       ()

        self.execPython  (fs['script'].value)

    def fnConfigure (self, path) :

        """

        @type   path    : List
        @param  path    : Split CGI execution path
        """

        fs = self.getFieldStorage ()

        sys.stdin  = self.rfile
        sys.stdout = self.wfile

        self.setIPTables    ()
        print "OK"

    def fnCGI (self, path) :

        """
        Execute python code passed as a file attached as the \em script
        parameter as a CGI script, ie., the script executes as if under
        a web server. Resource limits are applied, and the user and group
        are set.

        @type   path    : List
        @param  path    : Split CGI execution path
        """

        #  In order that the code can retrieve the CGI parameters
        #  for itself, while the code here can retrieve the 'script'
        #  parameter, we read the remaining input from the client and
        #  replicate it for use locally and in the script.
        #
        if self.m_cgi_fp :
            qs = self.rfile.read (int(self.headers['content-length']))
            self.m_cgi_fp = StringIO.StringIO (qs)
            self.rfile    = StringIO.StringIO (qs)

        fs = self.getFieldStorage()

        #  The environment of the script is updated with the stored
        #  values. Note that we cannot simply do:
        #
        #  os.environ = self.m_cgi_env
        #
        #  since the cgi.FieldStorage constructor can be passed a
        #  specific environment, but which defaults in the constructor
        #  arguments as ( ... environ = os.environ, ... ) which
        #  resolves when the code is loaded and not when it is
        #  executed.
        #
        for key, value in self.m_cgi_env.items() :
            os.environ[key] = value
        sys.stdin  = self.rfile
        sys.stdout = self.wfile

        #  Apply resource limits, and set group and user.
        #
        self.setIPTables    ()
        self.setRLimit      ()
        self.setGroup       ()
        self.setUser        ()
        self.addPaths       ()
        self.addEnvironment ()
        self.setScraperID   ()
        self.setRunID       ()

        self.execPython  (fs['script'].value)



class ControllerHTTPServer \
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
    Execute controller.

    @type   port    : Integer
    @param  port    : Port on which to listen
    """
    ScraperController.protocol_version = "HTTP/1.0"

    httpd = ControllerHTTPServer(('', port), ScraperController)
    sa    = httpd.socket.getsockname()
    sys.stdout.write ("Serving HTTP on %s port %s\n" % ( sa[0], sa[1] ))
    sys.stdout.flush ()

    httpd.serve_forever()


def autoFirewall () :

    """
    Setup firewall when the firewall=auto option is selected.
    """

    rules = []
    firewallBegin (rules)
    firewallEnd   (rules)
    firewallSetup (rules, sys.stdout, sys.stderr)

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
    try    : os.remove (varDir + '/run/controller.pid')
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

        if arg[: 9] == '--varDir='  :
            varDir  = arg[ 9:]
            continue

        if arg[ :9] == '--config='  :
            confnam = arg[ 9:]
            continue

        if arg[ :7] == '--name='  :
            name    = arg[ 7:]
            continue

        if arg[:10] == '--addPath=' :
            sys.path.append (arg[10:])
            continue

        if arg[:11] == '--firewall=' :
            firewall = arg[11:]
            continue

        if arg == '--subproc' :
            subproc = True
            continue

        if arg == '--daemon'  :
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
            sys.stdout = open (varDir + '/log/controller', 'w', 0)
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

        pf = open (varDir + '/run/controller.pid', 'w')
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

    config = ConfigParser.ConfigParser()
    config.readfp (open(confnam))

    if firewall == 'auto' :
        autoFirewall ()

    if name is None :
        name = socket.gethostname()
    execute (config.getint (name, 'port'))
