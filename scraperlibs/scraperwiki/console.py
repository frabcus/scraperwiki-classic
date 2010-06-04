try:
  import json
except:
  import simplejson as json

logfd = None

def setConsole (_logfd) :

    global logfd
    logfd = _logfd

def dumpMessage (**message) :

    logfd.write (json.dumps (message) + '\n')

def logScrapedURL (url, length) :

    dumpMessage (message_type = 'sources', url = url, content = "%d bytes from %s" % (length, url))

def logScrapedURLError (url) :

    dumpMessage (message_type = 'sources', url = url, content = "Failed: %s" % url)

def logScrapedData (pdata) :

    dumpMessage (message_type = 'data', content = pdata)

def logMessage (message) :

    dumpMessage (message_type = 'console', content = message)

def logWarning (message) :

    dumpMessage (message_type = 'console', content = 'Warning: ' + message)
