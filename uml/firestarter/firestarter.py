import sys
import resource
import string
import time
import inspect
import os
import hashlib
import ConfigParser
import urllib
import urllib2
import cStringIO
import socket

try:    import simplejson as json
except: import json

class FireStarter:

    """
    This class provides an interface to the FireBox UML subsystem. The
    mechanism is to create an instance of this class, set the required
    options, and then execute it. The result from the execution call is
    the output from whatever is run under the controller in the UML
    box.
    """

    def __init__(self, config) :
        self.m_conf = ConfigParser.ConfigParser()
        self.m_conf.readfp(open(config))
        self.m_error       = None
        self.soc_file = None

    def execute(self, jdata):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            dhost = self.m_conf.get('dispatcher', 'host')
            dport = self.m_conf.getint('dispatcher', 'port')
            soc.connect((dhost, dport))
        except:
            return self

        # this runID is incredibly ugly, unnecessarily long, and will be prepended with "draft" for draft modes
        # also gets "fromfrontend" prepended when the running of a script from the webpage
        s = hashlib.sha1()
        s.update(str(os.urandom(16)))
        s.update(str(os.getpid()))
        s.update(str(time.time()))
        jdata["runid"] = '%.6f_%s' % (time.time(), s.hexdigest())
        if jdata.get("draft"):
            jdata["runid"] = "draft|||%s" % jdata["runid"]

        # the sys.path added internally into the controller (strange configuration)
        jdata["paths"] = [ ]
        if self.m_conf.has_option ('dispatcher', 'path') :
            for path in self.m_conf.get('dispatcher', 'path').split(','):
                if path:
                    jdata["paths"].append(path)

        jdata["white"] = [ ]
        jdata["black"] = [ ]
        confurl = self.m_conf.get('dispatcher', 'confurl')
        conftxt = "white=.*"  # hard code the whitelist to avoid accessing it (better for local versions)
        if confurl != "allwhite":
            try:
                conftxt = urllib2.urlopen(confurl).read().replace('\r', '')
            except IOError:
                if confurl[:26] != 'http://dev.scraperwiki.com':    # known problem
                    print json.dumps({ 'message_type':'console', 'content': "Failed to open: %s" % confurl })
        for line in conftxt.split('\n'):
            kv = line.split('=')
            if len(kv) == 2 and kv[0] in ['white', 'black']:
                jdata[kv[0]].append(kv[1])

        sdata = json.dumps(jdata)
        soc.send('POST /Execute HTTP/1.1\r\n')
        soc.send('Content-Length: %s\r\n' % len(sdata))
        soc.send('Connection: close\r\n')

        # these parameters are lifted out by the dispatcher for its operation until we can get to the bottom of what's going on with _read_write
        soc.send("x-scraperid: %s\r\n" % jdata["scraperid"])
        soc.send("x-testname: %s\r\n" % jdata["scrapername"])
        soc.send("x-runid: %s\r\n" % jdata["runid"])
        
        soc.send('\r\n')
        soc.send(sdata)

        self.soc_file = soc.makefile('r')
        status_line = self.soc_file.readline()
        if status_line.split(' ')[1] != '200':
            self.m_error = status_line.split(' ', 2)[2].strip()
            self.soc_file.close()
            return self

        while True: # Ignore the HTTP headers
            line = self.soc_file.readline()
            if line.strip() == "":
                break

        return self

    def __iter__(self):
        return self

        # returning content
    def next(self):
        if self.m_error:
            message = json.dumps({'message_type' : 'fail', 'content' : self.m_error})
            self.m_error = None
            return message
        elif self.soc_file and not self.soc_file.closed:
            line = self.soc_file.readline().strip()
            if line == '':
                self.soc_file.close()
                raise StopIteration
            else:
                return line
        else:
            raise StopIteration


