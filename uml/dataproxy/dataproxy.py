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

try   : import json
except: import simplejson as json

import datalib

USAGE      = " [--varDir=dir] [--subproc] [--daemon] [--config=file]"
child      = None

parser = optparse.OptionParser()
parser.add_option("--varDir", metavar="dir", default='/var')
parser.add_option("--subproc", action="store_true")
parser.add_option("--daemon", action="store_true")
parser.add_option("--uid")
parser.add_option("--gid")
parser.add_option("--config", dest="confnam", metavar="file", default='uml.cfg')
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.confnam))


class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    __base         = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle  = __base.handle

    server_version = "DataProxy/ScraperWiki_0.0.1"
    rbufsize       = 0

    def log_message (self, format, *args) :
        BaseHTTPServer.BaseHTTPRequestHandler.log_message(self, format, *args)
        sys.stderr.flush()

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

    def process(self, db, dataauth, runID, short_name, request):
        #print "rrr", request
        if type(request) != dict:
            res = {"error":'request must be dict', "content":str(request)}
        elif "maincommand" not in request:
            res = {"error":'request must contain maincommand', "content":str(request)}
            
        elif request["maincommand"] == 'clear_datastore':
            res = db.clear_datastore(short_name)
        
        elif request["maincommand"] == 'sqlitecommand':
            if request["command"] == "downloadsqlitefile":
                res = db.downloadsqlitefile(short_name, seek=request["seek"], length=request["length"])
            else:
                res = db.sqlitecommand(dataauth, runID, short_name, command=request["command"], val1=request["val1"], val2=request["val2"])
        
        elif request["maincommand"] == 'save_sqlite':
            res = db.save_sqlite(runID, short_name, unique_keys=request["unique_keys"], data=request["data"], swdatatblname=request["swdatatblname"])
        
        else:
            res = {"error":'Unknown maincommand: %s' % request["maincommand"]}
        
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

        db = datalib.Database(self, config.get('dataproxy', 'resourcedir'))
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
                        self.process(db, dataauth, runID, short_name, request)
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
    try    : os.kill(child, signal.SIGTERM)
    except : pass
    try    : os.remove(poptions.varDir + '/run/dataproxy.pid')
    except : pass
    sys.exit (1)


if __name__ == '__main__' :

    #  If executing in daemon mode then fork and detatch from the
    #  controlling terminal. Basically this is the fork-setsid-fork
    #  sequence.
    #
    if poptions.daemon :
        if os.fork() == 0 :
            os .setsid()
            sys.stdin  = open ('/dev/null')
            sys.stdout = open (poptions.varDir + '/log/dataproxy', 'a', 0)
            sys.stderr = sys.stdout
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

        pf = open (poptions.varDir + '/run/dataproxy.pid', 'w')
        pf.write  ('%d\n' % os.getpid())
        pf.close  ()

    if poptions.gid is not None:
        os.setregid(int(poptions.gid), int(poptions.gid))
    if poptions.uid is not None:
        os.setreuid(int(poptions.uid), int(poptions.uid))

    #  If running in subproc mode then the server executes as a child
    #  process. The parent simply loops on the death of the child and
    #  recreates it in the event that it croaks.
    if poptions.subproc:
        signal.signal(signal.SIGTERM, sigTerm)
        while True:
            child = os.fork()
            if child == 0:
                break

            sys.stdout.write("%s: Forked subprocess: %d\n" % (datetime.datetime.now().ctime(), child))
            sys.stdout.flush()
            os.wait()


    port = config.getint('dataproxy', 'port')
    ProxyHandler.protocol_version = "HTTP/1.0"
    httpd = ProxyHTTPServer(('', port), ProxyHandler)
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()
