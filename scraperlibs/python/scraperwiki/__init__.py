import base64

try    : import json
except : import simplejson as json


logfd = None   # set to os.fdopen(3, 'w', 0) for consuming json objects

def dumpMessage(d):
    val = json.dumps(d)
    logfd.write( "%s\n" % (val,) )
    logfd.flush()


def writeBinaryData(data):
    msg = {'message_type': 'console', 'encoding': 'base64', 'content': base64.encodestring(data)})
    logfd.write( "%s\n" % (json.dumps(msg),) )
    logfd.flush()


from utils import log, scrape, pdftoxml, swimport
import geo
import datastore
import sqlite
import metadata
import stacktrace

