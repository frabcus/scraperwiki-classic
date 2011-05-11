#!/usr/bin/env python
import sys
import os
import optparse
import hashlib
import urllib2
import ConfigParser
import socket
import time

try:    import simplejson as json
except: import json

#  You can test this script by typing:
#       echo "print 1" | python runner.py

configfile = '/var/www/scraperwiki/uml/uml.cfg'

parser = optparse.OptionParser()
parser.add_option("--guid")
parser.add_option("--language", default='python')
parser.add_option("--name", default='', metavar="SCRAPER_NAME")
parser.add_option("--cpulimit", default='80')
parser.add_option("--urlquery", default='')
parser.add_option("--draft", action="store_true", default=False)


class FireStarter:
    def __init__(self, dhost, dport, jdata):
        self.m_error = None
        self.soc_file = None
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((dhost, dport))

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

        # Ignore the HTTP headers
        while True: 
            line = self.soc_file.readline()
            if line.strip() == "":
                break


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




def buildjdata(code, options, config):
    jdata = { "user":"nobody", "group":"nogroup" }
    jdata["code"] = code.replace('\r', '')
    jdata["cpulimit"] = int(options.cpulimit)
    jdata["draft"] = options.draft
    jdata["language"] = options.language
    jdata["scraperid"] = options.guid
    jdata["urlquery"] = options.urlquery
    jdata["scrapername"] = options.name

    # set the runid
    s = hashlib.sha1()
    s.update(str(os.urandom(16)))
    s.update(str(os.getpid()))
    s.update(str(time.time()))
    jdata["runid"] = '%.6f_%s' % (time.time(), s.hexdigest())
    if jdata.get("draft"):
        jdata["runid"] = "draft|||%s" % jdata["runid"]

    # the sys.path added internally into the controller (strange configuration)
    jdata["paths"] = [ ]
    if config.has_option ('dispatcher', 'path') :
        for path in config.get('dispatcher', 'path').split(','):
            if path:
                jdata["paths"].append(path)

    # set the white and blacklists
    jdata["white"] = [ ]
    jdata["black"] = [ ]
    confurl = config.get('dispatcher', 'confurl')
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

    return jdata


# main loop
if __name__ == "__main__":
    options, args = parser.parse_args()
    code = sys.stdin.read()
    config = ConfigParser.ConfigParser()
    config.readfp(open(configfile))
    jdata = buildjdata(code, options, config)

    dhost = config.get('dispatcher', 'host')
    dport = config.getint('dispatcher', 'port')
    fs = FireStarter(dhost, dport, jdata)
    
    for message in fs:
        sys.stdout.write(message + '\r\n')
        sys.stdout.flush()
