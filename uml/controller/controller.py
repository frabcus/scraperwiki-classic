#!/bin/sh -
"exec" "python" "$0" "$@"

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
import select
import string
import StringIO
import resource
import subprocess
import re
import cgi
import ConfigParser

try    : import json
except : import simplejson as json

global  confnam
global  config
global  firewall
global  wfmap

USAGE       = " [--varDir=dir] [--addPath=path] [--subproc] [--daemon] [--firewall=option] [--config=file] [--name=name]"
child       = None
varDir      = '/var'
confnam     = 'uml.cfg'
config      = None
name        = None
firewall    = None
re_resolv   = re.compile ('nameserver\s+([0-9.]+)')
setuid      = True
wfmap       = {}

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
                     shell  = True,
                     stdin  = open('/dev/null'),
                     stdout = stdout,
                     stderr = stderr
        )
        p.wait ()

    os.remove   (rname)


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
        self.m_stdout       = sys.stdout
        self.m_stderr       = sys.stderr
        self.m_scraperID    = None
        self.m_runID        = None

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

        if setuid and 'x-setuser'  in self.headers :
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

        if setuid and 'x-setgroup' in self.headers :
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
            self.m_scraperID = os.environ['SCRAPER_GUID'] = self.headers['x-scraperid']

    def setRunID (self) :

        """
        If the \em x-runid header is present then set that as the run ID.
        """

        if 'x-runid'      in self.headers :
            self.m_runID     = os.environ['RUNID']        = self.headers['x-runid']

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

#   def setIPTables (self) :
#
#       """
#       Set up IPTables firewalling. The firewall rules, as \em iptables command
#       arguments, are passed as headers starting 'x-iptables-'. These are written
#       to a temporary file which is used as input to the \em iptables-restore
#       command.
#       """
#
#       if os.getuid() != 0 :
#           return
#       if 'x-noiptables' in self.headers :
#           return
#       if firewall != 'request' :
#           return
#
#       rules = []
#       firewallBegin (rules)
#       for name, value in self.headers.items() :
#           if name[:11] == 'x-iptables-' :
#               rfile.write (value + '\n')
#       firewallEnd   (rules)
#       firewallSetup (rules, self.wfile. self.wfile)

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

        @rtype      : String
        @return     : Traceback mode
        """

        for name, value in self.headers.items() :
            if name == 'x-traceback' :
                return value
        return 'text'

    def sendWhoAmI (self, query) :

        """
        Send controller information, useful for debugging.

        @type   query   : String
        @param  query   : 
        """

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')
        self.connection.send  ('hostname=%s\n' % socket.gethostname())

    def sendIdent (self, query) :

        """
        Send ident information, specifically the scraper and run identifiers for a
        specified connection to the proxy.

        @type   query   : String
        @param  query   : (remote:local) ports from the proxy's viewpoint
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
#       p    = re.compile ('python *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
        p    = re.compile ('exec.[a-z]+ *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
        lsof = subprocess.Popen([ 'lsof', '-n', '-P' ], stdout = subprocess.PIPE).communicate()[0]
        for line in lsof.split('\n') :
            m = p.match (line)
            if m :
                self.log_request('Ident', '(%s,%s) is pid %s' % (lport, rport, m.group(1)))
                try    : self.connection.send (open('/tmp/ident.%s' % m.group(1)).read())
                except : self.log_request('Ident', '(%s,%s) send failed' % (lport, rport))
                return
        self.log_request('Ident', '(%s,%s) not found' % (lport, rport))

    def sendNotify (self, query) :

        """
        Send notification back through the controller.

        @type   query   : String
        @param  query   : (remote:local) ports from the proxy's viewpoint
        """

        params = cgi.parse_qs(query)
        try    :
            wfile = wfmap[params['runid'][0]]
            msg   = {}
            for key, value in params.items() :
                if key != 'runid' :
                    msg[key] = value[0]
            line  = json.dumps(msg) + '\n'
            wfile.write (line)
            wfile.flush ()
        except :
            pass

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')


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

        if path == '/WhoAmI' :
            self.sendWhoAmI (query)
            self.connection.close()
            return

        if path == '/Ident'  :
            self.sendIdent  (query)
            self.connection.close()
            return

        if path == '/Notify' :
            self.sendNotify (query)
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

    def execScript (self, lsfx, code, pwfd, lwfd) :

        """
        Execute a python script, passed as the text of the script. If the
        script throws an exception then generate a traceback, preceeded
        by a delimiter.
        """

        tap      = config.get (socket.gethostname(), 'tap')
        httpport = config.get ('httpproxy', 'port')
        ftpport  = config.get ('ftpproxy',  'port')
        dshost   = config.get ('dataproxy', 'host')
        dsport   = config.get ('dataproxy', 'port')

        args    = \
                [   'exec.%s' % lsfx,
                    '--http=http://%s:%s'       % (tap,  httpport),
                    '--https=http://%s:%s'      % (tap,  httpport),
                    '--ftp=ftp://%s:%s'         % (tap,  ftpport ),
                    '--ds=%s:%s'                % (dshost, dsport),
                    '--path=%s'                 % string.join(sys.path, ':'),
                    '--script=/tmp/scraper.%d'  % os.getpid(),
                ]

        try    : args.append ('--cache=%s' % self.headers['x-cache'    ])
        except : pass
        try    : args.append ('--trace=%s' % self.headers['x-traceback'])
        except : args.append ('--trace=text')

        os.close (0)
        os.close (1)
        os.close (2)
        os.open  ('/dev/null', os.O_RDONLY)
        os.dup2  (pwfd, 1)
        os.dup2  (lwfd, 2)
        os.close (pwfd)
        os.close (lwfd)

        os.execvp('exec.%s' % lsfx, args)

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
        self.setRLimit      ()
        self.setGroup       ()
        self.setUser        ()
        self.addPaths       ()
        self.addEnvironment ()
        self.setScraperID   ()
        self.setRunID       ()

        p = subprocess.Popen \
        (   command,
            shell   = True,
            stdin   = open('/dev/null'),
            stdout  = self.wfile,
            stderr  = self.wfile
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

        self.setScraperID   ()
        self.setRunID       ()

        ppipe = os.pipe()
        lpipe = os.pipe()
        pid   = os.fork()

        if pid > 0 :

            cltime1 = time.time()
            wfmap[self.m_runID] = self.wfile

            import swlogger
            swl = swlogger.SWLogger(config)
            swl.connect ()
            swl.log     (self.m_scraperID, self.m_runID, 'C.START')

            #  Close the write sides of the pipes, these are only needed in the
            #  child processes.
            #
            os.close (ppipe[1])
            os.close (lpipe[1])

            #  Create file-like objects so that we can use readline. These are
            #  stored mapped from the file descriptors for convenient access
            #  below.
            #
            fdmap = {}
            fdmap[ppipe[0]] = os.fdopen(ppipe[0], 'r')
            fdmap[lpipe[0]] = os.fdopen(lpipe[0], 'r')

            #  Create a polling object and register the two pipe read descriptors
            #  for input. We will loop reading and processing data from these.
            #
            p   = select.poll()
            p.register (ppipe[0], select.EPOLLIN)
            p.register (lpipe[0], select.EPOLLIN)

            #  Loop while the file descriptors are still open in the child
            #  process. Output is passed back, with "print" output jsonified.
            #  Check for exception messages, in which case log the exception to
            #  the logging database.
            #
            busy = 2
            while busy > 0 :
                for e in p.poll() :
                    if e[0] in fdmap :
                        line = fdmap[e[0]].readline()
                        if line == '' :
                            p.unregister (e[0])
                            busy -= 1
                            continue
                        if e[0] == ppipe[0] :
                            msg  = { 'message_type' : 'console', 'content' : line[:100] }
                            if len(line) >= 100 :
                                msg['content_long'] = line
                            line = json.dumps(msg) + '\n'
                        self.wfile.write (line)
                        self.wfile.flush ()
                        if e[0] == lpipe[0] :
                            msg = json.loads(line)
                            if msg['message_type'] == 'exception' :
                                swl.log (self.m_scraperID, self.m_runID, 'C.ERROR', arg1 = msg['content'], arg2 = msg['content_long'])

            #  Capture the child user and system times as best we can, since this
            #  is summed over all children.
            #
            ostimes1   = os.times ()
            os.wait()
            ostimes2   = os.times ()
            cltime2    = time.time()
            swl.log (self.m_scraperID, self.m_runID, 'C.END',   arg1 = ostimes2[2] - ostimes1[2], arg2 = ostimes2[3] - ostimes1[3])

            msg = '%d seconds elapsed, used %d CPU seconds' %  \
                                    (   int(cltime2 - cltime1),
                                        int(ostimes2[2] - ostimes1[2])
                                    )
            self.wfile.write \
                (   json.dumps \
                    (   {   'message_type'  : 'console',
                            'content'       : msg,
                        }
                    )   + '\n'
                )
            del wfmap[self.m_runID]

            try    : os.remove ('/tmp/scraper.%d' % pid)
            except : pass
            try    : os.remove ('/tmp/ident.%d'   % pid)
            except : pass
            return

        if pid < 0 :
            return

        os.close (ppipe[0])
        os.close (lpipe[0])

        fs = self.getFieldStorage ()

        idents = []
        if self.m_scraperID is not None : idents.append ('scraperid=%s' % self.m_scraperID)
        if self.m_runID     is not None : idents.append ('runid=%s'     % self.m_runID    )
        for name, value in self.headers.items() :
            if name[:17] == 'x-addallowedsite-' :
                idents.append ('allow=%s' % value)
                continue
            if name[:17] == 'x-addblockedsite-' :
                idents.append ('block=%s' % value)
                continue

        open ('/tmp/ident.%d'   % os.getpid(), 'w').write(string.join(idents, '\n'))
        open ('/tmp/scraper.%d' % os.getpid(), 'w').write(fs['script'].value)

        os.environ['metadata_host' ] = config.get ('metadata', 'host')

        #  Apply resource limits, set group and user, paths and
        #  environment.
        #
        self.setRLimit      ()
        self.setGroup       ()
        self.setUser        ()
        self.addPaths       ()
        self.addEnvironment ()

        try    : language = self.headers['x-language']
        except : language = 'python'

        if language == 'python' :
            self.execScript  ('py',  fs['script'].value, ppipe[1], lpipe[1])
            return

        if language == 'php'    :
            self.execScript  ('php', fs['script'].value, ppipe[1], lpipe[1])
            return

        self.wfile.write \
                    (   json.dumps \
                        (   {   'message_type'  : 'console',
                                'content'       : 'Language %s not recognised' % language,
                            }
                        )   + '\n'
                    )
        self.wfile.flush ()
        os.exit()


class ControllerHTTPServer \
        (   SocketServer.ThreadingMixIn,
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

        if arg == '--nosetuid':
            setuid = False
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
