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
import threading

try    : import json
except : import simplejson as json

global  confnam
global  config
global  firewall
global  scrapersByRunID
global  scrapersByPID
global  lock

USAGE           = " [--varDir=dir] [--addPath=path] [--subproc] [--daemon] [--firewall=option] [--config=file] [--name=name]"
child           = None
varDir          = '/var'
confnam         = 'uml.cfg'
config          = None
name            = None
firewall        = None
re_resolv       = re.compile ('nameserver\s+([0-9.]+)')
setuid          = True
scrapersByRunID = {}
scrapersByPID   = {}
lock            = threading.Lock()

infomap     = {}

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
        self.m_urlquery     = None
        self.m_uid          = None
        self.m_gid          = None
        self.m_paths        = []

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

    def checkUser (self) :

        """
        If the \em x-setuser header is present then use that for the real and
        effective user.
        """

        if setuid and 'x-setuser'  in self.headers :
            import pwd
            try    :
                self.m_uid = pwd.getpwnam (self.headers['x-setuser' ]).pw_uid
            except :
                self.send_error (404, 'User %s not found'  % self.headers['x-setuser' ])
                return False
        return True

    def checkGroup (self) :

        """
        If the \em x-setgroup header is present then use that for the real and
        effective group.
        """

        if setuid and 'x-setgroup' in self.headers :
            import grp
            try    :
                self.m_gid = grp.getgrnam (self.headers['x-setgroup']).gr_gid
            except :
                self.send_error (404, 'Group %s not found' % self.headers['x-setgroup'])
                return False
        return True

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

    def setUrlquery (self) :

        """
        If the \em x-urlquery header is present then set that as the urlquery
        """

        if 'x-urlquery'   in self.headers :
            self.m_urlquery  = os.environ['URLQUERY']        = self.headers['x-urlquery']

    
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

    def addPaths (self) :

        """
        Add directories to the search path.
        command.
        """

        for name, value in self.headers.items() :
            if name[:8] == 'x-paths-' :
                self.m_paths.append (value)

    def addEnvironment (self) :

        """
        Add stuff to the environment
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

    def sendStatus (self, query) :

        """
        Send status information, useful for debugging.

        @type   query   : String
        @param  query   : 
        """

        status = []
        lock.acquire()
        for key, value in scrapersByRunID.items() :
            status.append ('runID=%s' % (key))
        lock.release()

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')
        self.connection.send  (string.join (status, '\n') + '\n')

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
        #  process number; this is used to map to the identification information for
        #  the scraper.
        #
        (lport, rport) = string.split (query, ':')
        p    = re.compile ('exec.[a-z]+ *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
        lsof = subprocess.Popen([ 'lsof', '-n', '-P' ], stdout = subprocess.PIPE).communicate()[0]
        for line in lsof.split('\n') :
            m = p.match (line)
            if m :
                self.log_request('Ident', '(%s,%s) is pid %s' % (lport, rport, m.group(1)))
                try    :
                    info = scrapersByPID[int(m.group(1))]
                    self.connection.send (string.join(info['idents'], '\n'))
                    self.connection.send ("\n")
                    for key, value in info['options'].items() :
                        self.connection.send ('option=%s:%s\n' % (key, value))
                except Exception, e:
                    self.log_request('Ident', '(%s,%s) send failed: %s' % (lport, rport, repr(e)))
                return
        self.log_request('Ident', '(%s,%s) not found' % (lport, rport))

    def sendNotify (self, query) :

        """
        Send notification back through the controller.

        @type   query   : String
        @param  query   : URL-encoded message data plus runid
        """

        params  = cgi.parse_qs(query)
        wfile   = None
        try     :
            lock.acquire()
            wfile = scrapersByRunID[params['runid'][0]]['wfile']
        finally :
            lock.release()

        if wfile is not None :
            msg   = {}
            for key, value in params.items() :
                if key != 'runid' :
                    msg[key] = value[0]
            line  = json.dumps(msg) + '\n'
            wfile.write (line)
            wfile.flush ()

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')

    def sendOption (self, query) :

        """
        Set option

        @type   query   : String
        @param  query   : URL-encoded options data plus runid
        """

        params  = cgi.parse_qs(query)
        options = None
        try     :
            lock.acquire()
            options = scrapersByRunID[params['runid'][0]]['options']
        finally :
            lock.release()

        if options is not None :
            for key, value in params.items() :
                if key != 'runid' :
                    options[key] = value[0]

        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')
        for key, value in options.items() :
            self.connection.send ("%s=%s\n" % (key, value))

        self.log_request('Option', '')

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

        if path == '/Status' :
            self.sendStatus (query)
            self.connection.close()
            return

        if path == '/Notify' :
            self.sendNotify (query)
            self.connection.close()
            return

        if path == '/Option' :
            self.sendOption (query)
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
        httpport = config.get ('webproxy',  'port')
        ftpport  = config.get ('ftpproxy',  'port')
        dshost   = config.get ('dataproxy', 'host')
        dsport   = config.get ('dataproxy', 'port')

        args    = \
                [   'exec.%s' % lsfx,
                    '--http=http://%s:%s'       % (tap,  httpport),
                    '--https=http://%s:%s'      % (tap,  httpport),
                    '--ftp=ftp://%s:%s'         % (tap,  ftpport ),
                    '--ds=%s:%s'                % (dshost, dsport),
                    '--path=%s'                 % string.join(self.m_paths, ':'),
                    '--script=/tmp/scraper.%d'  % os.getpid(),
                ]

        if self.m_uid is not None : args.append ('--uid=%d' % self.m_uid)
        if self.m_gid is not None : args.append ('--gid=%d' % self.m_gid)

        try    : args.append ('--cache=%s' % self.headers['x-cache'    ])
        except : pass
        try    : args.append ('--trace=%s' % self.headers['x-traceback'])
        except : args.append ('--trace=text')

        os.close (0)
        os.close (1)
        os.close (2)
        os.close (3)
        os.open  ('/dev/null', os.O_RDONLY)
        os.dup2  (pwfd, 1)
        os.dup2  (pwfd, 2)
        os.dup2  (lwfd, 3)
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
        self.setUrlquery    ()

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

        if not self.checkUser () : return
        if not self.checkGroup() : return

        self.setScraperID   ()
        self.setRunID       ()
        self.setUrlquery    ()

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

        fs = self.getFieldStorage ()

        psock = socket.socketpair()
        lpipe = os.pipe()
        pid   = os.fork()

        if pid > 0 :

            cltime1 = time.time()
            lock.acquire()
            info    = { 'wfile' : self.wfile, 'idents' : idents, 'options' : {} }
            scrapersByRunID[self.m_runID] = info
            scrapersByPID  [pid         ] = info
            lock.release()

            try :

                import swlogger
                swl = swlogger.SWLogger(config)
                swl.connect ()
                swl.log     (self.m_scraperID, self.m_runID, 'C.START')

                #  Close the write sides of the pipes, these are only needed in the
                #  child processes.
                #
                psock[1].close()
                os.close(lpipe[1])

                #  Create file-like objects so that we can use readline. These are
                #  stored mapped from the file descriptors for convenient access
                #  below.
                #
                fdmap = {}
                fdmap[psock[0].fileno()] = [ psock[0], '' ]
                fdmap[lpipe[0]         ] = [ lpipe[0], '' ]

                #  Create a polling object and register the two pipe read descriptors
                #  for input. We will loop reading and processing data from these. Also
                #  poll the connection; this will be flagged as having input if it is
                #  closed at the other end.
                #
                p   = select.poll()
                p.register (psock[0].fileno(),        select.POLLIN)
                p.register (lpipe[0],                 select.POLLIN)
                p.register (self.connection.fileno(), select.POLLIN)

                #  Loop while the file descriptors are still open in the child
                #  process. Output is passed back, with "print" output jsonified.
                #  Check for exception messages, in which case log the exception to
                #  the logging database. If the caller closes the connection,
                #  kill the child and exit the loop.
                #
                busy    = 2
                while busy > 0 :
                    for e in p.poll() :
                        fd = e[0]
                        #
                        #  If the event is on the caller connection then caller must
                        #  have terminated, so exit loop.
                        #
                        if fd == self.connection.fileno() :
                            busy = 0
                            os.kill (pid, signal.SIGKILL)
                            break
                        #
                        #  Otherwise should have been from child ...
                        #
                        if fd in fdmap :
                            #
                            #  Read some text. If none then the child has closed the connection
                            #  so unregister here and decrement count of open child connections.
                            #
                            try    : line = fdmap[fd][0].recv(8192)
                            except : line = os.read (fdmap[fd][0], 8192)
                            if line == '' :
                                p.unregister (fd)
                                busy -= 1
                            #
                            #  If data received and data does not end in a newline the add to
                            #  any prior data from the connection and loop.
                            #
                            if len(line) > 0 and line[-1] != '\n' :
                                fdmap[fd][1] = fdmap[fd][1] + line
                                continue
                            #
                            #  Prepend prior data to the current data and clear the prior
                            #  data. If still nothing then loop.
                            #
                            line = fdmap[fd][1] + line
                            fdmap[fd][1] = ''
                            if line == '' :
                                continue
                            #
                            #  If data is from the print connection then json-format as a console
                            #  message; data from logging connection should be already formatted.
                            #
                            if fd == psock[0].fileno() :
                                msg  = { 'message_type' : 'console', 'content' : line }
                                line = json.dumps(msg) + '\n'
                            #
                            #  Send data back towards the client.
                            #
                            self.wfile.write (line)
                            self.wfile.flush ()
                            #
                            #  If the data came from the logging connection and was an error the
                            #  log to the database. We might get multiple json'd lines in one
                            #  so split up.
                            #
                            if fd == lpipe[0] :
                                for l in string.split(line, '\n') :
                                    if l != '' :
                                        msg = json.loads(l)
                                        if msg['message_type'] == 'exception' :
                                            swl.log (self.m_scraperID, self.m_runID, 'C.ERROR', arg1 = msg['content'], arg2 = msg['content_long'])

                #  Capture the child user and system times as best we can, since this
                #  is summed over all children.
                #
                ostimes1   = os.times ()
                os.waitpid(pid, 0)
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
                                'message_sub_type'  : 'consolestatus',  # should be made into message_type
                                'content'       : msg,
                            }
                        )   + '\n'
                    )

            except Exception, e :

                self.log_request('Copying results failed: %s' % repr(e))

            finally :

                lock.acquire()
                del scrapersByRunID[self.m_runID]
                del scrapersByPID  [pid         ]
                lock.release()

                #  Make absolutely sure all sockets and pipes are closed, since we are
                #  running in a thread and not a separate process.
                #
                try    : psock[0].close()
                except : pass
                try    : psock[1].close()
                except : pass
                try    : os.close(lpipe[0])
                except : pass
                try    : os.close(lpipe[1])
                except : pass

                try    : os.remove ('/tmp/scraper.%d' % pid)
                except : pass
                try    : os.remove ('/tmp/ident.%d'   % pid)
                except : pass

            return

        if pid < 0 :
            return

        #  Code from here down runs in the child process
        #
        psock[0].close()
        os.close(lpipe[0])

        open ('/tmp/ident.%d'   % os.getpid(), 'w').write(string.join(idents, '\n'))
        open ('/tmp/scraper.%d' % os.getpid(), 'w').write(fs['script'].value)

        os.environ['metadata_host' ] = config.get ('metadata', 'host')

        #  Apply resource limits, set group and user, paths and
        #  environment.
        #
        self.setRLimit      ()
        self.addPaths       ()
        self.addEnvironment ()

        try    : language = self.headers['x-language']
        except : language = 'python'

        if language == 'python' :
            self.execScript  ('py',  fs['script'].value, psock[1].fileno(), lpipe[1])
            return

        if language == 'php'    :
            self.execScript  ('php', fs['script'].value, psock[1].fileno(), lpipe[1])
            return

        if language == 'ruby'   :
            self.execScript  ('rb',  fs['script'].value, psock[1].fileno(), lpipe[1])
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

    rules    = []
    natrules = []

    rules.append ('*filter')
    rules.append ('-A OUTPUT -p tcp -d 127.0.0.1 -j ACCEPT'       )
    rules.append ('-A OUTPUT -p tcp -d %s -j ACCEPT'              % (config.get (socket.gethostname(), 'host')))
    rules.append ('-A OUTPUT -p tcp -d %s -j ACCEPT'              % (config.get (socket.gethostname(), 'tap' )))
    rules.append ('-A OUTPUT -p tcp -d %s -j ACCEPT'              % (config.get (socket.gethostname(), 'eth' )))
    rules.append ('-A OUTPUT -p tcp -d %s --dport %s -j ACCEPT'   % (config.get ('httpproxy',  'host'), config.get ('httpproxy',  'port')))
    rules.append ('-A OUTPUT -p tcp -d %s --dport %s -j ACCEPT'   % (config.get ('httpsproxy', 'host'), config.get ('httpsproxy', 'port')))
    rules.append ('-A OUTPUT -p tcp -d %s --dport %s -j ACCEPT'   % (config.get ('webproxy',   'host'), config.get ('webproxy',   'port')))
    rules.append ('-A OUTPUT -p tcp -d %s --dport %s -j ACCEPT'   % (config.get ('dataproxy',  'host'), config.get ('dataproxy',  'port')))
    rules.append ('-A OUTPUT -p tcp -d %s --dport 3306 -j ACCEPT' % (config.get ('dataproxy',  'host')))
    for line in open ('/etc/resolv.conf').readlines() :
        m = re_resolv.match (line)
        if m :
            rules.append ('-A OUTPUT -p udp -d %s --dport 53 -j ACCEPT' % m.group(1))
    rules.append ('-A OUTPUT -j REJECT')
    rules.append ('COMMIT')

    natrules.append   ('*nat')
    host = config.get ('httpproxy',  'host')
    port = config.get ('httpproxy',  'port')
    natrules.append   ('-A OUTPUT -s ! %s -p tcp --dport 80  -j DNAT --to %s:%s' % (host, host, port))
    host = config.get ('httpsproxy', 'host')
    port = config.get ('httpsproxy', 'port')
    natrules.append   ('-A OUTPUT -s ! %s -p tcp --dport 443 -j DNAT --to %s:%s' % (host, host, port))
    natrules.append   ('COMMIT')

    rname = '/tmp/iptables.%s' % os.getpid()
    rfile = open (rname, 'w')
    rfile.write  (string.join (rules, '\n') + '\n')
    rfile.close  ()

    if os.getuid() == 0 :

        p = subprocess.Popen \
                (    'iptables-restore < %s' % rname,
                     shell  = True,
                     stdin  = open('/dev/null'),
                     stdout = sys.stdout,
                     stderr = sys.stderr
        )
        p.wait ()

    rname = '/tmp/iptables_nat.%s' % os.getpid()
    rfile = open (rname, 'w')
    rfile.write  (string.join (natrules, '\n') + '\n')
    rfile.close  ()

    if os.getuid() == 0 :

        p = subprocess.Popen \
                (    'iptables-restore --table nat < %s' % rname,
                     shell  = True,
                     stdin  = open('/dev/null'),
                     stdout = sys.stdout,
                     stderr = sys.stderr
        )
        p.wait ()

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
