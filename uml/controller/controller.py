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
import StringIO
import resource
import subprocess
import re
import cgi
import ConfigParser
import threading
import optparse
import pwd
import grp
import logging
import logging.config

try    : import json
except : import simplejson as json

global  scrapersByRunID
global  scrapersByPID
global  lock

child           = None

re_resolv       = re.compile ('nameserver\s+([0-9.]+)')
scrapersByRunID = {}
scrapersByPID   = {}
lock            = threading.Lock()

infomap     = {}

parser = optparse.OptionParser()
parser.add_option("--firewall", metavar="option")
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--setuid", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

logging.config.fileConfig(poptions.config)
logger = logging.getLogger('controller')

#stdoutlog = open('/var/www/scraperwiki/uml/var/log/controller.log'+"-stdout", 'a', 0)
stdoutlog = sys.stdout


# one of these per scraper executing the code and relaying it to the scrapercontroller
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
        self.m_stdout       = sys.stdout
        self.m_stderr       = sys.stderr

        BaseHTTPServer.BaseHTTPRequestHandler.__init__ (self, *alist, **adict)


    def sendConnectionHeaders(self):
        self.connection.send  ('HTTP/1.0 200 OK\n')
        self.connection.send  ('Connection: Close\n')
        self.connection.send  ('Pragma: no-cache\n')
        self.connection.send  ('Cache-Control: no-cache\n')
        self.connection.send  ('Content-Type: text/text\n')
        self.connection.send  ('\n')

    def sendStatus(self, query) :
        status = []
        lock.acquire()
        for key, value in scrapersByRunID.items() :
            status.append ('runID=%s' % (key))
        lock.release()

        self.sendConnectionHeaders()
        self.connection.send('\n'.join(status) + '\n')

    def sendIdent (self, query) :
        self.sendConnectionHeaders()

        #  The query contains the proxy's remote port (which is the local port here)
        #  and the proxy's local port (which is the remote port here). Scan all open
        #  files for a TCP/IP stream with these two ports. If found then extract the
        #  process number; this is used to map to the identification information for
        #  the scraper.
        #
        (lport, rport) = query.split(':')
        # On Linux, process names come out as exec.py/exec.rb etc.
        # On OSX, they come out as python/ruby etc.
        # XXX todo, get PHP working on OSX
        p    = re.compile ('(?:exec.[a-z]+|[Pp]ython|[Rr]uby) *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
        lsof = subprocess.Popen([ 'lsof', '-n', '-P', '-i' ], stdout = subprocess.PIPE).communicate()[0]
        for line in lsof.split('\n') :
            m = p.match (line)
            if m :
                logger.debug('Ident (%s,%s) is pid %s' % (lport, rport, m.group(1)))
                try    :
                    info = scrapersByPID[int(m.group(1))]
                    self.connection.send ('\n'.join(info['idents']))
                    self.connection.send ("\n")
                except Exception, e:
                    logger.exception('Ident (%s,%s) send failed')
                return
        logger.warning('Ident (%s,%s) not found:\n%s' % (lport, rport, lsof))

    def sendNotify (self, query) :
        """
        Send notification back through the controller. (usually of a http request)
        """
        params  = cgi.parse_qs(query)
        wfile   = None
        try     :
            lock.acquire()
            wfile = scrapersByRunID[params['runid'][0]]['wfile']
        except  :
            logger.exception("test3")
            pass
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

        self.sendConnectionHeaders()

    # this request is put together by runner.py
    def do_POST (self) :
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(self.path, 'http')
        assert path == '/Execute'
            # BaseHTTPRequestHandler.rfile is the input stream
        request = json.loads(self.rfile.read(int(self.headers['content-length'])))
        self.execute(request)

    def do_GET (self) :
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse (self.path, 'http')

        if path == '/Ident':
            self.sendIdent(query)
        elif path == '/Status':
            self.sendStatus(query)
        elif path == '/Notify':    # used to relay notification of http requests back to the dispatcher
            self.sendNotify(query)
        else:
            self.send_error(404, 'Action %s not found' % path)
            return

        self.connection.close()



# one of these per scraper receiving the data
class ScraperController (BaseController) :

    def saveunicode(self, text):
        try:     return unicode(text)
        except UnicodeDecodeError:     pass
        try:     return unicode(text, encoding='utf8')
        except UnicodeDecodeError:     pass
        try:     return unicode(text, encoding='latin1')
        except UnicodeDecodeError:     pass
        return unicode(text, errors='replace')
 
 
    def processmain(self, psock, lpipe, pid, cltime1):
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

        #  Loop while the file descriptors are still open in the child
        #  process. Output is passed back, with "print" output jsonified.
        #  Check for exception messages, in which case log the exception to
        #  the logging database. If the caller closes the connection,
        #  kill the child and exit the loop.
        #
        busy    = 2
        while busy > 0 :
            #  Create a list of the two pipe read descriptors that are still
            #  open for input via select. We loop reading and processing data
            #  from these. Also poll the connection; this will be flagged as
            #  having input if it is closed at the other end.
            rlist = fdmap.keys() + [self.connection.fileno(),]
            (rback, wback, eback) = select.select(rlist, [], []) 
            assert wback == [] # we don't use these, only read
            assert eback == [] # we don't use these, only read

            for fd in rback:
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
                    mapped = fdmap[fd]
                    #
                    #  Read some text. If none then the child has closed the connection
                    #  so unregister here and decrement count of open child connections.
                    #
                    line = None
                    if line is None :
                        if hasattr(mapped[0], "recv"):
                            line = mapped[0].recv(8192) # socket
                        else:
                            line = os.read (mapped[0], 8192) # pipe
                    if line in [ '', None ] :
                        # 
                        # In case of echoing console output (for PHP, or for
                        # Ruby/Python before the ConsoleStream is set up in
                        # exec.py/rb), send anything left over that didn't end in a \n
                        # 
                        if fd == psock[0].fileno() :
                            if mapped[1] != '':
                                # XXX this repeats the code below, there's probably a
                                # better way of structuring it
                                msg  = { 'message_type' : 'console', 'content' : self.saveunicode(mapped[1]) + "\n"}
                                mapped[1] = ''
                                text = json.dumps(msg) + '\n'
                                self.wfile.write (text)
                                self.wfile.flush ()
                        #
                        # Record done with that pipe
                        #
                        del fdmap[fd]
                        busy -= 1
                        continue
                    #
                    #  If data received and data does not end in a newline the add to
                    #  any prior data from the connection and loop.
                    #
                    if len(line) > 0 and line[-1] != '\n' :
                        mapped[1] = mapped[1] + line
                        continue
                    #
                    #  Prepend prior data to the current data and clear the prior
                    #  data. If still nothing then loop.
                    #
                    text = mapped[1] + line
                    mapped[1] = ''
                    if text == '' :
                        continue
                    #
                    #  If data is from the print connection then json-format as a console
                    #  message; data from logging connection should be already formatted.
                    #
                    if fd == psock[0].fileno() :
                        msg  = { 'message_type' : 'console', 'content' : self.saveunicode(text) }
                        text = json.dumps(msg) + '\n'
                    #
                    #  Send data back towards the client.
                    #
                    self.wfile.write (text)
                    self.wfile.flush ()
                    #
                    #  If the data came from the logging connection and was an error the
                    #  log to the database. We might get multiple json'd lines in one
                    #  so split up.
                    #
                    if fd == lpipe[0] :
                        for l in text.split('\n') :
                            if l != '' :
                                msg = json.loads(l)

        #  Capture the child user and system times as best we can, since this
        #  is summed over all children.
        #
        ostimes1   = os.times ()
        (waited_pid, waited_status) = os.waitpid(pid, 0)
        ostimes2   = os.times ()
        cltime2    = time.time()

        # this creates the status output that is passed out to runner.py.  
        # The actual completion signal comes when the runner.py process ends
        msg =       {   'message_type'    : 'executionstatus',
                        'content'         : 'runcompleted', 
                        'elapsed_seconds' : int(cltime2 - cltime1), 
                        'CPU_seconds'     : int(ostimes2[2] - ostimes1[2])
                    }
        if os.WIFEXITED(waited_status):
            msg['exit_status'] = os.WEXITSTATUS(waited_status)
        if os.WIFSIGNALED(waited_status):
            msg['term_sig'] = os.WTERMSIG(waited_status)
            # generate text version (e.g. SIGSEGV rather than 11)
            sigmap = dict((k, v) for v, k in signal.__dict__.iteritems() if v.startswith('SIG'))
            if msg['term_sig'] in sigmap:
                msg['term_sig_text'] = sigmap[msg['term_sig']]
        self.wfile.write(json.dumps(msg) + '\n')
         
 
    def processchild(self, psock, lpipe, idents, request):
        psock[0].close()
        os.close(lpipe[0])

        open ('/tmp/ident.%d'   % os.getpid(), 'w').write('\n'.join(idents))
        open ('/tmp/scraper.%d' % os.getpid(), 'w').write(request['code'].encode('utf-8'))

        paths = request.get("paths", [ ])
        language = request.get('language', 'python')
        resource.setrlimit(resource.RLIMIT_CPU, (request['cpulimit'], request['cpulimit']+1))

        # language extensions
        lsfx = { 'php':'php', 'ruby':'rb', 'python':'py' }[language]
        
        pwfd = psock[1].fileno()
        lwfd = lpipe[1]
        
        tap      = config.get (socket.gethostname(), 'tap')
        # webport = config.get ('webproxy',  'port')   # no longer used and useless
            # httpport, httpsport passed in and only used in debug versions as there is a new lower level method that 
            # intercepts the ports from within the UML configurations
        httpport = config.get ('httpproxy',  'port')
        httpsport = config.get ('httpsproxy',  'port')
        ftpport  = config.get ('ftpproxy',  'port')
        dshost   = config.get ('dataproxy', 'host')
        dsport   = config.get ('dataproxy', 'port')

        execscript = os.path.join(os.path.dirname(sys.argv[0]), 'exec.%s' % lsfx)
        args    = \
                [   execscript,
                    '--http=http://%s:%s'       % (tap,  httpport),
                    '--https=http://%s:%s'      % (tap,  httpsport),
                    '--ftp=ftp://%s:%s'         % (tap,  ftpport ),
                    '--ds=%s:%s'                % (dshost, dsport),
                    '--path=%s' % ':'.join(paths),
                    '--script=/tmp/scraper.%d'  % os.getpid(),
                ]

        if poptions.setuid:
            args.append('--uid=%d' % pwd.getpwnam("nobody").pw_uid)
            args.append('--gid=%d' % grp.getgrnam("nogroup").gr_gid)


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

        # the actual execution of the scraper
        os.execvp(execscript, args)

 
    def execute(self, request):
        logger.debug('Execute %s' % str(request)[:100])

        idents = []
        if request.get("scraperid"):
            idents.append('scraperid=%s' % request.get("scraperid"))
            os.environ['SCRAPER_GUID'] = request.get("scraperid")

        self.m_runID = None
        if request.get("runid"):
            idents.append ('runid=%s' % request.get("runid"))
            os.environ['RUNID'] = request.get("runid")
            self.m_runID = request.get("runid")

        if request.get("scrapername"):
            idents.append ('scrapername=%s' % request.get("scrapername"))
            os.environ['SCRAPER_NAME'] = request.get("scrapername")

        if request.get("urlquery"):
            os.environ['URLQUERY'] = request.get("urlquery")
            os.environ['QUERY_STRING'] = request.get("urlquery")

        #print request, idents
        for value in request['white']:
            idents.append('allow=%s' % value)
        for value in request['black']:
            idents.append('block=%s' % value)

        psock = socket.socketpair()
        lpipe = os.pipe()
        pid   = os.fork()

        if pid > 0 :
            cltime1 = time.time()
            lock.acquire()
            info = { 'wfile' : self.wfile, 'idents' : idents }
            scrapersByRunID[self.m_runID] = info
            scrapersByPID[pid] = info
            lock.release()

            try:
                self.processmain(psock, lpipe, pid, cltime1)

            except Exception, e:
                logger.exception('Copying results failed')

            finally:
                lock.acquire()
                del scrapersByRunID[self.m_runID]
                del scrapersByPID  [pid         ]
                lock.release()

                #  Make absolutely sure all sockets and pipes are closed, since we are
                #  running in a thread and not a separate process.
                #
                try    : psock[0].close()
                except :
                    logger.exception("test")
                    pass
                try    : psock[1].close()
                except : 
                    logger.exception("test2")
                    pass
                try    : os.close(lpipe[0])
                except OSError: pass
                try    : os.close(lpipe[1])
                except OSError: pass

                try    : os.remove ('/tmp/scraper.%d' % pid)
                except OSError: pass
                try    : os.remove ('/tmp/ident.%d'   % pid)
                except OSError: pass

            return

        if pid == 0:
            self.processchild(psock, lpipe, idents, request)


# one of these representing the whole controller
class ControllerHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """
    Wrapper class providing a forking server. Note that we run forking
    and not threaded as we may want to change the user and group id of
    the executed scripts.
    """
    pass


def autoFirewall():
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
    rules.append ('-A OUTPUT -p icmp -j ACCEPT')
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
    rfile.write  ('\n'.join(rules) + '\n')
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
    rfile.write  ('\n'.join(natrules) + '\n')
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


def sigTerm(signum, frame):
    os.kill(child, signal.SIGTERM)
    try:
        os.remove(poptions.pidfile)
    except OSError:
        pass  # no such file
    sys.exit (1)


def execute(port) :
    ScraperController.protocol_version = "HTTP/1.0"
    httpd = ControllerHTTPServer(('', port), ScraperController)
    sa = httpd.socket.getsockname()
    logger.info("Serving HTTP on %s port %s" % ( sa[0], sa[1] ))
    httpd.serve_forever()

if __name__ == '__main__' :
    # daemon
    if os.fork() == 0 :
        os .setsid()
        sys.stdin  = open ('/dev/null')
        sys.stdout = stdoutlog
        sys.stderr = stdoutlog
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

    pf = open(poptions.pidfile, 'w')
    pf.write('%d\n' % os.getpid())
    pf.close()


    # subproc
    signal.signal (signal.SIGTERM, sigTerm)
    while True :
        child = os.fork()
        if child == 0 :
            break
        logger.info("Forked subprocess: %d" % child)
        os.wait()
        logger.warning("Forked subprocess ended: %d" % child)

    if poptions.firewall == 'auto' :
        autoFirewall()
    
    execute(config.getint(socket.gethostname(), 'port'))
    
    
