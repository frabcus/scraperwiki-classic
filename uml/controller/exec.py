#!/usr/bin/python -W ignore::DeprecationWarning

import  sys
import  os

# moved to the top because syntax errors in the scraperlibs otherwise are difficult to detect
#
sys.stdout = os.fdopen(1, 'w', 0)
sys.stderr = os.fdopen(2, 'w', 0)

import  socket
import  signal
import  string
import  time
import  urllib2
import  ConfigParser


try    : import json
except : import simplejson as json


USAGE       = ' [--cache=N] [--trace=mode] [--script=name] [--path=path] [--scraperid=id] [--runid=id] [--urlquery=str] [-http=proxy] [--https=proxy] [--ftp=proxy] [--ds=server:port]'
cache       = None
trace       = None
script      = None
path        = None
scraperID   = None
runID       = None
urlquery    = None
httpProxy   = None
httpsProxy  = None
ftpProxy    = None
datastore   = None
uid         = None
gid         = None

for arg in sys.argv[1:] :

    if arg[: 8] == '--cache='       :
        cache      = int(arg[ 8:])
        continue

    if arg[: 8] == '--trace='       :
        trace      = arg[ 8:]
        continue

    if arg[: 9] == '--script='      :
        script     = arg[ 9:]
        continue

    if arg[:12] == '--scraperid='   :
        scraperID  = arg[12:]
        continue

    if arg[: 8] == '--runid='       :
        runID      = arg[ 8:]
        continue

    if arg[: 11] == '--urlquery='       :
        urlquery   = arg[ 11:]
        continue
    
    if arg[: 7] == '--path='        :
        path       = arg[ 7:]
        continue

    if arg[: 7] == '--http='        :
        httpProxy  = arg[ 7:]
        continue

    if arg[: 8] == '--https='       :
        httpsProxy = arg[ 8:]
        continue

    if arg[: 6] == '--ftp='         :
        ftpProxy   = arg[ 6:]
        continue

    if arg[: 5] == '--ds='          :
        datastore  = arg[ 5:]
        continue

    if arg[: 6] == '--uid='         :
        uid        = arg[ 6:]
        continue

    if arg[: 6] == '--gid='         :
        gid        = arg[ 6:]
        continue

    print "usage: " + sys.argv[0] + USAGE
    sys.exit (1)

if gid is not None :
    os.setregid (int(gid), int(gid))
if uid is not None :
    os.setreuid (int(uid), int(uid))

if path is not None :
    for p in string.split (path, ':') :
        sys.path.append (p)


#  Imports cannot be done until sys.path is set
#
import  scraperwiki.utils
import  scraperwiki.datastore
import  scraperwiki.console
import  scraperwiki.stacktrace

scraperwiki.console.logfd   = os.fdopen(3, 'w', 0)

sys.stdout  = scraperwiki.console.ConsoleStream (scraperwiki.console.logfd)
sys.stderr  = scraperwiki.console.ConsoleStream (scraperwiki.console.logfd)

config = ConfigParser.ConfigParser()
config.add_section ('dataproxy')
config.set         ('dataproxy', 'host', string.split(datastore, ':')[0])
config.set         ('dataproxy', 'port', string.split(datastore, ':')[1])


#  These seem to be needed for urllib.urlopen() to support proxying, though
#  FTP doesn't actually work.
#

# uncomment the following line and the ProxyHandler lines if you want proxying to work 
# in a local version

        # This is not used in the real deployed version as it uses another lower level method within the UMLs
        # ... although it does not appear to have been built for ftp (so you might not get ftp for PHP version)
##os.environ['http_proxy' ] = httpProxy
##os.environ['https_proxy'] = httpsProxy
os.environ['ftp_proxy'  ] = ftpProxy
scraperwiki.utils.urllibSetup   ()

#  This is for urllib2.urlopen() (and hence scraperwiki.scrape()) where
#  we can set explicit handlers.
#
scraperwiki.utils.urllib2Setup \
    (
##        urllib2.ProxyHandler ({'http':  httpProxy }),
##        urllib2.ProxyHandler ({'https': httpsProxy}),
        urllib2.ProxyHandler ({'ftp':   ftpProxy  })
    )

if cache is not None :
    scraperwiki.utils.allowCache (cache)

#  Pass the configuration to the datastore. At this stage no connection
#  is made; a connection will be made on demand if the scraper tries
#  to save anything.
#
scraperwiki.datastore.DataStore (config)



#  Set up a CPU time limit handler which simply throws a python
#  exception.
#
# (technical question: what happens if the user script traps this exception and ignores it? --JGT)
# (answer: it will be brutally killed when the hard CPU time limit is reached.
# See "man setrlimit", "If the process continues to consume CPU time, it will
# be sent  SIGXCPU once per second until the hard limit is reached, at which
# time it is sent SIGKILL". This is one second later, as the runner does
# "fs.setCPULimit      (cpulimit, cpulimit+1)". --FAI)
def sigXCPU (signum, frame) :
    raise Exception ("ScraperWiki CPU time exceeded")
signal.signal (signal.SIGXCPU, sigXCPU)


code = open(script).read()
try :
    import imp
    mod        = imp.new_module ('scraper')
    exec code.rstrip() + "\n" in mod.__dict__

except Exception, e :
    etb = scraperwiki.stacktrace.getExceptionTraceback(code)  
    assert etb.get('message_type') == 'exception'
    scraperwiki.console.dumpMessage(etb)


sys.stdout.flush()
sys.stderr.flush()
