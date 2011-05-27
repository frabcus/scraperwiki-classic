#!/usr/bin/env python
import sys
import os
import optparse
import urllib2
import ConfigParser
import socket
import time
import logging
import logging.config
import uuid

try:    import simplejson as json
except: import json

#  You can test this script by typing:
#       echo "print 1" | python runner.py

configfile = '/var/www/scraperwiki/uml/uml.cfg'

parser = optparse.OptionParser()
parser.add_option("--guid", default='')
parser.add_option("--language", default='python')
parser.add_option("--name", default='', metavar="SCRAPER_NAME")
parser.add_option("--cpulimit", default='80')
parser.add_option("--urlquery", default='')
parser.add_option("--draft", action="store_true", default=False)
options, args = parser.parse_args()

logging.config.fileConfig(configfile)
logger = logging.getLogger('runner')

config = ConfigParser.ConfigParser()
config.readfp(open(configfile))


def writereadstream(dhost, dport, jdata):
    soc_file = None
    
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect((dhost, dport))

    sdata = json.dumps(jdata)

    soc.send('POST /Execute HTTP/1.1\r\n')
    soc.send('Content-Length: %s\r\n' % len(sdata))
    soc.send('Connection: close\r\n')
    soc.send('\r\n')
    soc.sendall(sdata)

    
    sbuffer = [ ]
    bgap = False
    nbytes, nrecords = 0, 0
    while True:
        srec = soc.recv(8192)
        ssrec = srec.split("\n")  # multiple strings if a "\n" exists
        sbuffer.append(ssrec.pop(0))
        while ssrec:
            line = "".join(sbuffer)
            if line.strip():
                if not bgap:
                    pass # logger.debug("hhh: "+line)   # discard headers
                else:
                    sys.stdout.write(line + '\r\n')
                    sys.stdout.flush()
                    nbytes += len(line)
                    nrecords += 1
            else:
                bgap = True
            sbuffer = [ ssrec.pop(0) ]  # next one in
        if not srec:
            break
    
    logger.debug('%s:  ending %d bytes  %d records  %s' % (jdata["scrapername"], nbytes, nrecords, jdata["runid"]))
            
    if False:
        soc_file.close()
        logger.warning('fail on %s: %s' % (jdata["scrapername"], str(status_line)))
        sys.stdout.write(json.dumps({'message_type' : 'fail', 'content' : status_line[2].strip()}) + '\r\n')
        sys.stdout.flush()


def buildjdata(code, options, config):
    jdata = { }
    jdata["code"] = code.replace('\r', '')
    jdata["cpulimit"] = int(options.cpulimit)
    jdata["draft"] = options.draft
    jdata["language"] = options.language
    jdata["scraperid"] = options.guid
    jdata["urlquery"] = options.urlquery
    jdata["scrapername"] = options.name

    # set the runid
    jdata["runid"] = '%.6f_%s' % (time.time(), uuid.uuid4())
    if jdata.get("draft"):
        jdata["runid"] = "draft|||%s" % jdata["runid"]

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
    code = sys.stdin.read()
    jdata = buildjdata(code, options, config)
    logger.debug('%s: starting   %s' % (jdata["scrapername"], jdata["runid"]))

    dhost = config.get('dispatcher', 'host')
    dport = config.getint('dispatcher', 'port')
    writereadstream(dhost, dport, jdata)
