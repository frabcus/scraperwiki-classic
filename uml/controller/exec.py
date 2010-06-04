#!/usr/bin/python -W ignore::DeprecationWarning

import  sys
import  os
import  socket
import  signal
import  string
import  time
import  urllib2
import  ConfigParser

try    : import json
except : import simplejson as json

USAGE       = ' [--cache=N] [--trace=mode] [--script=name] [--path=path] [--scraperid=id] [--runid=id] [-http=proxy] [--https=proxy] [--ftp=proxy] [--ds=server:port]'
cache       = None
trace       = None
script      = None
path        = None
scraperID   = None
runID       = None
httpProxy   = None
httpsProxy  = None
ftpProxy    = None
datastore   = None

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

    print "usage: " + sys.argv[0] + USAGE
    sys.exit (1)

if path is not None :
    for p in string.split (path, ':') :
        sys.path.append (p)

import  scraperwiki.utils
import  scraperwiki.datastore
import  scraperwiki.console


config = ConfigParser.ConfigParser()
config.add_section ('dataproxy')
config.set         ('dataproxy', 'host', string.split(datastore, ':')[0])
config.set         ('dataproxy', 'port', string.split(datastore, ':')[1])

#  These seem to be needed for urllib.urlopen() to support proxying, though
#  FTP doesn't actually work.
#
os.environ['http_proxy' ] = httpProxy
os.environ['https_proxy'] = httpsProxy
os.environ['ftp_proxy'  ] = ftpProxy
scraperwiki.utils.urllibSetup   ()

#  This is for urllib2.urlopen() (and hance scraperwiki.scrape()) where
#  we can set explicit handlers.
#
scraperwiki.utils.urllib2Setup \
    (   urllib2.ProxyHandler ({'http':  httpProxy }),
        urllib2.ProxyHandler ({'https': httpsProxy}),
        urllib2.ProxyHandler ({'ftp':   ftpProxy  })
    )

if cache is not None :
    scraperwiki.utils.allowCache (cache)

#  Pass the configuration to the datastore. At this stage no connection
#  is made; a connection will be made on demand if the scraper tries
#  to save anything.
#
scraperwiki.datastore.DataStore (config)

errfd = sys.stderr
scraperwiki.console.setConsole  (sys.stderr)
sys.stderr = sys.stdout

#  Set up a CPU time limit handler which simply throws a python
#  exception.
#
def sigXCPU (signum, frame) :
    raise Exception ("CPUTimeExceeded")

signal.signal (signal.SIGXCPU, sigXCPU)

def getTraceback (code) :

    """
    Get traceback information. Returns exception, traceback, the
    scraper file in whch the error occured and the line number.

    @return         : (exception, traceback, file, line)
    """

    if trace == 'text' :
        import backtrace
        return backtrace.backtrace ('text', code, context = 10)
    if trace == 'html' :
        import backtrace
        return backtrace.backtrace ('html', code, context = 10)

    import traceback
    tb = [ \
            string.replace (t, 'File "<string>"', 'Scraper')
            for t in traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            if string.find (t, 'Controller.py') < 0
          ]
    return str(sys.exc_type), string.join(tb, ''), None, None

def execute (code) :

    try :
        import imp
        mod        = imp.new_module ('scraper')
        exec code.rstrip() + "\n" in mod.__dict__
    except Exception, e :
        import errormapper
        emsg = errormapper.mapException (e)
        etext, trace, infile, atline = getTraceback (code)
        errfd.write \
            (   json.dumps \
                (   {   'message_type'  : 'exception',
                        'content'       : emsg,
                        'content_long'  : trace,
                        'filename'      : infile,
                        'lineno'        : atline
                    }
                )   + '\n'
            )
        sys.stdout.flush ()

execute (open(script).read())
