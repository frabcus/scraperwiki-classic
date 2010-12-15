try:
  import json
except:
  import simplejson as json

import  sys
import base64

logfd = sys.stderr

def setConsole (_logfd) :

    global logfd
    logfd = _logfd

def dumpMessage (**message) :

    logfd.write (json.dumps (message))
    logfd.write ('\n')
    logfd.flush()

def logScrapedURL (url, length) :

    dumpMessage (message_type = 'sources', url = url, content = "%d bytes from %s" % (length, url))

def logScrapedURLError (url) :

    dumpMessage (message_type = 'sources', url = url, content = "Failed: %s" % url)

def logScrapedData (pdata) :

    dumpMessage (message_type = 'data', content = pdata)

def logMessage (message) :

    dumpMessage (message_type = 'console', content = message)

def logBinaryMessage (message) :

    dumpMessage (message_type = 'console', content = base64.encodestring(message), encoding="base64")

def logHTTPResponseHeader (headerkey, headervalue) :

    dumpMessage (message_type = 'httpresponseheader', headerkey = headerkey, headervalue = headervalue)

def logWarning (message) :

    dumpMessage (message_type = 'console', content = 'Warning: ' + message)
