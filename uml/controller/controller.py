#!/usr/bin/env python

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
import optparse, pwd, grp
import logging, logging.config

try    : import json
except : import simplejson as json

child           = None

runidstocontrollers = {}   # { runid => ScraperController }
pidstorunids   = {}   # { pid => runid }

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

stdoutlog = None
#stdoutlog = open('/var/www/scraperwiki/uml/var/log/controller.log'+"-stdout", 'a', 0)


# one of these per scraper executing the code and relaying it to the scrapercontroller
class BaseController (BaseHTTPServer.BaseHTTPRequestHandler) :

    """
    Controller base class. This is derived from a base HTTP
    server class, and contains code to process and dispatch
    requests.
    """
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "Controller/ScraperWiki_0.0.1"
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

    def sendStatus(self):
        status = []
        runids = runidstocontrollers.keys()  # to protect from multithreading
        for runid in runids:
            status.append('runID=%s' % (runid))
        logger.info("Sending status "+str(status))
        self.sendConnectionHeaders()
        self.connection.sendall('\n'.join(status) + '\n')


    def find_process_for_port( self, lport ):
        """
        Use the ss command (from iproute) to show all of the HTTP requests 
        that are currently established along with the process info.
        """
        cmd = "ss -o state established '( dport = :http )' -p"
    
        try:
            # Launch the subprocess and read the output
            p = subprocess.Popen(cmd, stdout = subprocess.PIPE,shell=True)
            content = p.communicate()[0]
            p.wait()
        except Exception,e:
            print e
            return None

        
        for line in content.split('\n')[1:]:
            if ':%s' % lport in line:
                proc = " ".join(line.split()).split()[-1]
                if proc.startswith('users:(('):
                    # Strip the bit that isn't relevant
                    proc = proc[len('users:(('):-2]
                    return int(proc.split(',')[1])
                else:
                    # if we found the port but no process info we should bail
                    return None
        return None


    def sendIdent(self, query) :
        self.sendConnectionHeaders()

        # given the port and socket, find the pid holding it open using a grep on lsof
        (lport, rport) = query.split(':')
        # On Linux, process names come out as exec.py/exec.rb etc.
        # On OSX, they come out as python/ruby etc.
        # XXX todo, get PHP working on OSX
        pid = None
        
        pid = self.find_process_for_port( lport )
        if pid is None:
            logging.debug('Failed to find pid with "ss" so trying lsof -i')
            # If we can't find the pid from 'ss' then we should try lsof
            try:
                lsof = subprocess.Popen([ 'lsof','-i', ':%s' % lport ], stdout = subprocess.PIPE).communicate()[0]
                line = lsof.split('\n')[1]
                pid = int(line.split(' ')[1])
            except:
                logging.debug('Failed to find pid with lsof -i')
                
        if pid is None:
            logging.debug('Failed to find pid with "ss" so trying lsof')
            # If we can't find the pid from 'ss' then we should try lsof
            p    = re.compile ('(?:exec.[a-z]+|[Pp]ython|[Rr]uby) *([0-9]*).*TCP.*:%s.*:%s.*' % (lport, rport))
            lsof = subprocess.Popen([ 'lsof', '-n', '-P', '-i' ], stdout = subprocess.PIPE).communicate()[0]
            for line in lsof.split('\n') :
                m = p.match(line)
                if m:
                    pid = int(m.group(1))
                    break
        else:
            logging.debug('Found process using ss')            

        if pid:
            logger.debug(' Ident (%s,%s) is pid %s' % (lport, rport, pid))
            runid = pidstorunids.get(pid)
            controller = runidstocontrollers.get(runid)
            if controller:
                self.connection.sendall('\n'.join(controller.idents))
            else:
                logger.warning('Ident scraper not longer present for pid %s' % pid)
            return
        else:
            logger.warning(' Ident (%s,%s) not found:\n%s' % (lport, rport, lsof))

        # Send notification back through the controller to the dispatcher . (normally of a http request)
        # we find which controller socket to send it to from the runid
    def sendNotify(self, query):
        params = cgi.parse_qs(query)
        runid = params['runid'][0]
        controller = runidstocontrollers.get(runid)
        if controller:
            msg = {}
            for key, value in params.items() :
                if key != 'runid' :
                    msg[key] = value[0]
            line  = json.dumps(msg) + '\n'
            controller.connection.sendall(line)

        self.sendConnectionHeaders()

    # this request is put together by runner.py
    def do_POST (self) :
        scm, netloc, path, query, fragment = urlparse.urlsplit(self.path)
        assert path == '/Execute'
            # BaseHTTPRequestHandler.rfile is the input stream
        remlength = int(self.headers['Content-Length'])
        jincoming = []
        while True:
            sjincoming = self.connection.recv(remlength)
            if not sjincoming:
                break
            jincoming.append(sjincoming)
            remlength -= len(sjincoming)
            if remlength <= 0:
                break
        if remlength != 0:
            emsg = {"error":"incoming message incomplete", "headers":str(self.headers), "lengths":str(map(len, jincoming))}
            logger.error(str(emsg))
            self.connection.sendall(json.dumps(emsg) + '\n')
            self.connection.close()
            return

        request = json.loads("".join(jincoming))
        self.execute(request)   # actually runs everything


    def do_GET (self) :
        scm, netloc, path, query, fragment = urlparse.urlsplit(self.path)
        if path == '/Ident':
            self.sendIdent(query)
        elif path == '/Status':
            self.sendStatus()
        elif path == '/Notify':    # used to relay notification of http requests back to the dispatcher
            self.sendNotify(query)
        else:
            self.send_error(404, 'Action %s not found' % path)
        self.connection.close()


def saveunicode(text):
    try:     return unicode(text)
    except UnicodeDecodeError:     pass
    try:     return unicode(text, encoding='utf8')
    except UnicodeDecodeError:     pass
    try:     return unicode(text, encoding='latin1')
    except UnicodeDecodeError:     pass
    return unicode(text, errors='replace')



# one of these per scraper receiving the data
class ScraperController(BaseController):
 
            # takes the output from the exec.py process call and sends it out to the dispatcher
    def processrelayoutput(self, streamprintsin, streamjsonsin, childpid, scrapername):
        ostimes1 = os.times()
        
        rlist = [ self.connection, streamprintsin, streamjsonsin ] 
        printsbuffer = [ ]
        jsonsbuffer = [ ]
        
        while len(rlist) > 2 and self.connection in rlist:
            try:
                rback, wback, eback = select.select(rlist, [ ], [ ]) 
            
                # shouldn't be happening any more, but try to track down which it is when it does
            except select.error, e:   
                logger.warning("bad file descriptor childpid: %d"%childpid)
                logger.warning([streamprintsin.fileno(), streamjsonsin.fileno(), self.connection.fileno()]) 
                for fd in rlist:
                    if type(fd) == int:
                        fdn = fd
                    else:
                        fdn = fd.fileno()
                    try:
                        os.fstat(fdn)
                    except:
                        logger.exception("bad osserror: %d" % fdn)
                raise
            
            # further incoming signals (sometimes empty) from the controller can be assumed to be a termination message
            if self.connection in rback:
                line = self.connection.recv(200)
                if not line:
                    logger.debug("incoming connection to %s gone down, so killing exec process" % (scrapername, childpid))
                else:
                    logger.debug("got message to kill exec process %s  %s %d" % (str([line]), scrapername, childpid))
                os.kill(childpid, signal.SIGKILL)
                break
            
            jsonoutputlist = [ ]
            
            # batch up stdout streaming into console message if a block ends in \n
            if streamprintsin in rback:
                srecprints = streamprintsin.recv(8192)   # returns '' if nothing more to come
                printsbuffer.append(srecprints)
                if not srecprints or srecprints[-1] == '\n':
                    line = "".join(printsbuffer)
                    if line:
                        jsonoutputlist.append(json.dumps({ 'message_type':'console', 'content':saveunicode(line) }))
                    del printsbuffer[:]
                if not srecprints:
                    streamprintsin.close()
                    rlist.remove(streamprintsin)

            # valid json objects coming in from file descriptor 3
            if streamjsonsin in rback:
                srecjsons = streamjsonsin.recv(8192)
                if srecjsons:
                    ssrecjsons = srecjsons.split("\n")
                    jsonsbuffer.append(ssrecjsons.pop(0))
                    while ssrecjsons:
                        jsonoutputlist.append("".join(jsonsbuffer))
                        del jsonsbuffer[:]
                        jsonsbuffer.append(ssrecjsons.pop(0))
                else:
                    streamjsonsin.close()
                    rlist.remove(streamjsonsin)

            # output the sequence of valid json objects to the dispatcher delimited by \n
            try:
                for jsonoutput in jsonoutputlist:
                    self.connection.sendall(jsonoutput + '\n')
            except socket.error, e:
                logger.exception("socket error sending %s  %s" % (scrapername, jsonoutput[:1000]))
                return None

        ostimes2 = os.times()

        # return message if connection still good to add any termination conditions
        if self.connection not in rlist:
            return None
        return { 'message_type':'executionstatus', 'content':'runcompleted', 
                 'elapsed_seconds' : int(ostimes2[4] - ostimes1[4]), 'CPU_seconds':int(ostimes2[0] - ostimes1[0]) }

 
    def processrunscript(self, streamprintsout, streamjsonsout, request, tmpscriptfile):
        fout = open(tmpscriptfile, 'w')
        fout.write(request['code'].encode('utf-8'))
        fout.close()

        language = request.get('language', 'python')
        resource.setrlimit(resource.RLIMIT_CPU, (request['cpulimit'], request['cpulimit']+1))

        # language extensions
        lexec = { 'php':'exec.php', 'ruby':'exec.rb', 'python':'exec.py' }[language]
        
        execscript = os.path.join(os.path.dirname(sys.argv[0]), lexec)
        args = [    execscript,
                    '--ds=%s:%s' % (config.get('dataproxy', 'host'), config.get('dataproxy', 'port')),
                    '--script=%s' % tmpscriptfile,
               ]

        if poptions.setuid:
            args.append('--gid=%d' % grp.getgrnam("nogroup").gr_gid)
            args.append('--uid=%d' % pwd.getpwnam("nobody").pw_uid)

        # close the filenos for stdin, stdout, stderr, 3, and then over-load them with streamprintsout and streamjsonsout
        os.close(0)
        os.close(1)
        os.close(2)
        os.close(3)
        
        os.dup2(streamprintsout, 1)
        os.dup2(streamprintsout, 2)
        os.dup2(streamjsonsout, 3)
        
        os.close(streamprintsout)
        os.close(streamjsonsout)

            # the actual execution of the scraper (never returns)
        os.execvp(execscript, args)

 
    def execute(self, request):
        self.idents = []
        
        scraperguid = request.get("scraperid", "")
        self.idents.append('scraperid=%s' % scraperguid)
        self.m_runID = request.get("runid", "")
        self.idents.append ('runid=%s' % self.m_runID)
        scrapername = request.get("scrapername", "")
        self.idents.append ('scrapername=%s' % scrapername)
        urlquery = request.get("urlquery", "")
        for value in request['white']:
            self.idents.append('allow=%s' % value)
        for value in request['black']:
            self.idents.append('block=%s' % value)
        self.idents.append('')   # to get an extra \n at the end

        logger.debug('Execute %s' % scrapername)
        
        streamprintsin, streamprintsout = socket.socketpair()
        streamjsonsin, streamjsonsout = socket.socketpair()
        
        childpid = os.fork()
        
        if childpid == 0:
                # set the environment variables only in the child process
            os.environ['SCRAPER_GUID'] = scraperguid
            os.environ['RUNID'] = self.m_runID
            os.environ['SCRAPER_NAME'] = scrapername
            os.environ['URLQUERY'] = urlquery
            os.environ['QUERY_STRING'] = urlquery
            
            logger.debug('processexec: %s' % scrapername)
            streamprintsin.close()
            streamjsonsin.close()
            tmpscriptfile = '/tmp/scraper.%d' % os.getpid() 
            self.processrunscript(streamprintsout.fileno(), streamjsonsout.fileno(), request, tmpscriptfile)  
                # eventually calls execvp("php exec.php") and never returns
        
        else:
            logger.debug('childpid %s: %s' % (childpid, scrapername))
            runidstocontrollers[self.m_runID] = self
            pidstorunids[childpid] = self.m_runID

            streamprintsout.close()
            streamjsonsout.close()

            try:
                endingmessage = self.processrelayoutput(streamprintsin, streamjsonsin, childpid, scrapername)
            except Exception, e:
                logger.exception('process main exception: %s  %s' % (childpid, scrapername))
                endingmessage = None

            waited_pid, waited_status = os.waitpid(childpid, 0)
            exitmessage = { }
            if os.WIFEXITED(waited_status):
                exitmessage['exit_status'] = os.WEXITSTATUS(waited_status)
            if os.WIFSIGNALED(waited_status):
                exitmessage['term_sig'] = os.WTERMSIG(waited_status)
                sigmap = dict((k, v) for v, k in signal.__dict__.iteritems() if v.startswith('SIG'))
                if exitmessage['term_sig'] in sigmap:
                    exitmessage['term_sig_text'] = sigmap[exitmessage['term_sig']]
                    
            logger.debug("%s endmessage: %s  exitmessage: %s" % (scrapername, endingmessage, exitmessage))
            del runidstocontrollers[self.m_runID]
            del pidstorunids[childpid]

            if endingmessage:
                endingmessage.update(exitmessage)
                try:
                    self.connection.sendall(json.dumps(endingmessage) + '\n')
                except socket.error, e:
                    logger.exception("ending message error: %s" % scrapername)
                self.connection.close()

            streamprintsin.close()
            streamjsonsin.close()

            try:
                os.remove('/tmp/scraper.%d' % childpid)
            except OSError:
                logger.exception('failed to delete /tmp/scraper.%d' % childpid)



# Should this be ForkingMixIn?
class ControllerHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


def autoFirewall():
    re_resolv = re.compile('nameserver\s+([0-9.]+)')
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


    # subproc
    signal.signal(signal.SIGTERM, sigTerm)
    while True:
        child = os.fork()
        if child == 0 :
            break
        logger.info("Forked subprocess: %d" % child)
        os.wait()
        logger.warning("Forked subprocess ended: %d" % child)

    if poptions.firewall == 'auto' :
        autoFirewall()
    
    ScraperController.protocol_version = "HTTP/1.0"
    httpd = ControllerHTTPServer(('', config.getint(socket.gethostname(), 'port')), ScraperController)
    sa = httpd.socket.getsockname()
    logger.info("Serving HTTP on %s port %s" % (sa[0], sa[1]))
    httpd.serve_forever()
    
    
