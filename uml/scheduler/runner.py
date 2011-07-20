import urlparse
import os, sys, time, signal
import socket, select
import StringIO, resource
import re, cgi
import ConfigParser
import optparse, pwd, grp, uuid
import urllib2

from django.core.mail import send_mail, mail_admins

try    : import json
except : import simplejson as json

import threading
import logging

class Runner(object):
    
    def __init__( self, code='', config_dict={}, *args, **kwargs ):
        self.code   = code
        self.config_dict = config_dict
        super(Runner,self).__init__(*args, **kwargs)


    def build_run_data(self, options):
        data = { }
        data["code"]      = self.code.replace('\r', '')
        data["cpulimit"]  = int(options.get('cpulimit',80))
        data["draft"]     = options.get('draft',False)
        data["language"]  = options.get('language', 'python')
        data["scraperid"] = options.get('guid', '')
        data["urlquery"]  = options.get('urlquery', '')
        data["scrapername"] = options.get('name', '')

        # set the runid
        data["runid"] = '%.6f_%s' % (time.time(), uuid.uuid4())
        if data.get("draft"):
            data["runid"] = "draft|||%s" % data["runid"]

        confurl = self.config_dict['confurl']

        # set the white and blacklists
        data["white"] = [ ]
        data["black"] = [ ]
        conftxt = "white=.*"  # hard code the whitelist to avoid accessing it (better for local versions)
        if confurl != "allwhite":
            try:
                conftxt = urllib2.urlopen(confurl).read().replace('\r', '')
            except IOError:
                if confurl[:26] != 'http://dev.scraperwiki.com':    # known problem
                    logging.error( json.dumps({ 'message_type':'console', 'content': "Failed to open: %s" % confurl }) )
        for line in conftxt.split('\n'):
            kv = line.split('=')
            if len(kv) == 2 and kv[0] in ['white', 'black']:
                data[kv[0]].append(kv[1])
                
        return data

def execute_runner(dhost, dport, data):
    soc_file = None
    
    if data["language"] not in ["python", "php", "ruby"]:
        sys.stdout.write(json.dumps({'message_type' : 'fail', 'content' : "no such language %s" % data["language"]}) + '\r\n')
        sys.stdout.flush()
        return 
    
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        soc.connect((dhost, dport))
    except Exception, e:
        mail_admins(subject="SICK DISPATCHER", message='Failed to connect to dispatcher at (%s:%s)' % (dhost,dport,))
        return

    sdata = json.dumps(data)

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
            
    if False:
        soc_file.close()
        sys.stdout.write(json.dumps({'message_type' : 'fail', 'content' : status_line[2].strip()}) + '\r\n')
        sys.stdout.flush()
