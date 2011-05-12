##!/bin/sh -
"exec" "python" "-O" "$0" "$@"

import BaseHTTPServer
import SocketServer
import urllib
import urlparse
import cgi
import signal
import os
import sys
import time
import ConfigParser
import datetime
import optparse
import grp
import pwd
import rslogger   # made possible by PYTHONPATH environment variable
import datalib

try   : import json
except: import simplejson as json

# note: there is a symlink from /var/www/scraperwiki to the scraperwiki directory
# which allows us to get away with being crap with the paths

config = ConfigParser.ConfigParser()
config.readfp(open('/var/www/scraperwiki/uml/uml.cfg'))

child      = None

parser = optparse.OptionParser()
parser.add_option("--setuid", action="store_true")
parser.add_option("--pidfile")
parser.add_option("--logfile")
parser.add_option("--toaddrs", default="")
poptions, pargs = parser.parse_args()

logger = rslogger.getlogger(name="dataproxy", logfile=poptions.logfile, level='info', toaddrs=poptions.toaddrs.split(","))
datalib.logger = logger
stdoutlog = open(poptions.logfile+"-stdout", 'a', 0)

class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "DataProxy/ScraperWiki_0.0.1"
    rbufsize       = 0

    def ident(self, uml, port):
        runID       = None
        short_name = None

        host      = config.get(uml, 'host')
        via       = config.get(uml, 'via' )
        rem       = self.connection.getpeername()
        loc       = self.connection.getsockname()
        lident     = urllib.urlopen ('http://%s:%s/Ident?%s:%s' % (host, via, port, loc[1])).read()   

                # should be using cgi.parse_qs(query) technology here
        for line in lident.split('\n'):
            if line:
                key, value = line.split('=')
                if key == 'runid':
                    runID = value
                elif key == 'scrapername':
                    short_name = value

        return runID, short_name

    def process(self, db, request):
        logger.debug(str(("rrr", request)))
        if type(request) != dict:
            res = {"error":'request must be dict', "content":str(request)}
        elif "maincommand" not in request:
            res = {"error":'request must contain maincommand', "content":str(request)}
            
        elif request["maincommand"] == 'clear_datastore':
            res = db.clear_datastore()
        
        elif request["maincommand"] == 'sqlitecommand':
            if request["command"] == "downloadsqlitefile":
                res = db.downloadsqlitefile(seek=request["seek"], length=request["length"])
            elif request["command"] == "datasummary":
                res = db.datasummary(request.get("limit", 10))
            elif request["command"] == "attach":
                res = db.sqliteattach(request.get("name"), request.get("asname"))
            elif request["command"] == "commit":
                res = db.commit()
            elif request["command"] == "execute":
                            # this should contain the attach list with it
                res = db.sqliteexecute(val1=request["val1"], val2=request["val2"])
        
        elif request["maincommand"] == 'save_sqlite':
            res = db.save_sqlite(unique_keys=request["unique_keys"], data=request["data"], swdatatblname=request["swdatatblname"])
        
        else:
            res = {"error":'Unknown maincommand: %s' % request["maincommand"]}
        
        logger.debug(json.dumps(res))
        self.connection.send(json.dumps(res)+'\n')


        # this morphs into the long running two-way connection
    def do_GET (self) :
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(self.path, 'http')
        params = dict(cgi.parse_qsl(query))

        if 'short_name' in params:
            if self.connection.getpeername()[0] != config.get('dataproxy', 'secure') :
                self.connection.send(json.dumps({"error":"short_name only accepted from secure hosts"})+'\n')
                return
            short_name = params.get('short_name', '')
            runID = 'fromfrontend.%s.%s' % (short_name, time.time()) 
            dataauth = "fromfrontend"
        else :
            runID, short_name = self.ident(params['uml'], params['port'])
            if runID[:8] == "draft|||" and short_name:
                dataauth = "draft"
            else:
                dataauth = "writable"
        
        if path == '' or path is None :
            path = '/'

        if scm not in ['http', 'https'] or fragment :
            self.connection.send(json.dumps({"error":"Malformed URL %s" % self.path})+'\n')
            return

        db = datalib.Database(self, config.get('dataproxy', 'resourcedir'), short_name, dataauth, runID)
        self.connection.send(json.dumps({"status":"good"})+'\n')

                # enter the loop that now waits for single requests (delimited by \n) 
                # and sends back responses through a socket
                # all with json objects -- until the connection is terminated
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
                        self.process(db, request)
                    sbuffer = [ ssrec.pop(0) ]  # next one in
                if not srec:
                    break
                
        finally :
            self.connection.close()


    do_HEAD   = do_GET
    do_POST   = do_GET
    do_PUT    = do_GET
    do_DELETE = do_GET


class ProxyHTTPServer(SocketServer.ForkingMixIn, BaseHTTPServer.HTTPServer):
    pass

def sigTerm(signum, frame) :
    #logger.debug("terminating")    # many of these, only one terminated
    os.kill(child, signal.SIGTERM)
    os.remove(poptions.pidfile)
    logger.warning("terminated")
    sys.exit(1)

if __name__ == '__main__' :

    # daemon mode
    if os.fork() == 0 :
        os.setsid()
        sys.stdin  = open('/dev/null')
        sys.stdout = stdoutlog
        sys.stderr = stdoutlog
        if os.fork() == 0 :
            ppid = os.getppid()
            while ppid != 1 :
                time.sleep(1)
                ppid = os.getppid()
        else :
            os._exit (0)
    else :
        os.wait()
        sys.exit (1)

    pf = open(poptions.pidfile, 'w')
    pf.write('%d\n' % os.getpid())
    pf.close()
        

    if poptions.setuid:
        gid = grp.getgrnam("nogroup").gr_gid
        os.setregid(gid, gid)
        uid = pwd.getpwnam("nobody").pw_uid
        os.setreuid(uid, uid)

    # subproc mode
    signal.signal(signal.SIGTERM, sigTerm)
    while True:
        child = os.fork()
        if child == 0:
            break
        logger.warning("%s: Forked subprocess: %d\n" % (datetime.datetime.now().ctime(), child))
        os.wait()


    port = config.getint('dataproxy', 'port')
    ProxyHandler.protocol_version = "HTTP/1.0"
    httpd = ProxyHTTPServer(('', port), ProxyHandler)
    sa = httpd.socket.getsockname()
    logger.warning(str(("Serving HTTP on", sa[0], "port", sa[1], "...")))
    httpd.serve_forever()

