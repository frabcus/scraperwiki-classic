#!/usr/bin/php5
<?php

ini_set        ('include_path',  ini_get('include_path') . PATH_SEPARATOR . '/home/mike/ScraperWiki/scraperwiki/uml/controller') ;

#import  sys
#import  os
#import  socket
#import  signal
#import  string
#import  time
#import  urllib2
#import  ConfigParser
#
#try    : import json
#except : import simplejson as json
#
$USAGE       = ' [--cache=N] [--trace=mode] [--script=name] [--path=path] [--scraperid=id] [--runid=id] [-http=proxy] [--https=proxy] [--ftp=proxy] [--ds=server:port]' ;
$cache       = undef ;
$trace       = undef ;
$script      = undef ;
$path        = undef ;
$scraperID   = undef ;
$runID       = undef ;
$httpProxy   = undef ;
$httpsProxy  = undef ;
$ftpProxy    = undef ;
$datastore   = undef ;

for ($idx = 1 ; $idx < count($argv) ; $idx += 1)
{
   $arg  = $argv[$idx] ;

   if (substr ($arg, 0,  8) == '--cache='    )
   {
      $cache      = substr ($arg,  8) ;
      continue    ;
   }
   if (substr ($arg, 0,  8) == '--trace='    )
   {
      $trace      = substr ($arg,  8) ;
      continue    ;
   }
   if (substr ($arg, 0,  9) == '--script='   )
   {
      $script     = substr ($arg,  9) ;
      continue    ;
   }
   if (substr ($arg, 0, 12) == '--scraperid=')
   {
      $scraperID  = substr ($arg, 12) ;
      continue    ;
   }
   if (substr ($arg, 0,  8) == '--runid='    )
   {
      $runID      = substr ($arg,  8) ;
      continue    ;
   }
   if (substr ($arg, 0, 7) == '--path='      )
   {
      $path       = substr ($arg,  7) ;
      continue    ;
   }
   if (substr ($arg, 0, 7) == '--http='      )
   {
      $httpProxy  = substr ($arg,  7) ;
      continue    ;
   }
   if (substr ($arg, 0, 8) == '--https='     )
   {
      $httpsProxy = substr ($arg,  8) ;
      continue    ;
   }
   if (substr ($arg, 0, 6) == '--ftp='       )
   {
      $ftpProxy   = substr ($arg,  6) ;
      continue    ;
   }
   if (substr ($arg, 0, 5) == '--ds='        )
   {
      $datastore  = substr ($arg,  5) ;
      continue    ;
   }

   print "usage: " . $argv[0] . $USAGE . "\n" ;
   exit  (1) ;
}

function sw_dumpMessage ($dict)
{
   fwrite (STDERR, json_encode ($dict) . "\n") ;
}

function sw_logScrapedURL ($url, $length)
{
    sw_dumpMessage
      (  array
         (  'message_type' => 'sources',
            'url'          => $url,
            'content'      => sprintf ("%d bytes from %s", $length, $url)
      )  )  ;
}

function sw_scrape ($url)
{
   global $httpProxy ;

   $curl = curl_init ($url ) ;
   curl_setopt ($curl, CURLOPT_RETURNTRANSFER,  true      ) ;
   curl_setopt ($curl, CURLOPT_PROXY,           $httpProxy) ;
   $res  = curl_exec ($curl) ;

   curl_close ($curl) ;
   sw_logScrapedURL ($url, strlen($res)) ;
   return   $res  ;
}

function sw_data_save ($unique_keys, $data)
{
   sw_dumpMessage (array('message_type' => 'data', 'content' => $data)) ;
}

#
#if path is not None :
#    for p in string.split (path, ':') :
#        sys.path.append (p)
#
#import  scraperwiki.utils
#import  scraperwiki.datastore
#import  scraperwiki.console
#
#
#config = ConfigParser.ConfigParser()
#config.add_section ('dataproxy')
#config.set         ('dataproxy', 'host', string.split(datastore, ':')[0])
#config.set         ('dataproxy', 'port', string.split(datastore, ':')[1])
#
##  These seem to be needed for urllib.urlopen() to support proxying, though
##  FTP doesn't actually work.
##
#os.environ['http_proxy' ] = httpProxy
#os.environ['https_proxy'] = httpsProxy
#os.environ['ftp_proxy'  ] = ftpProxy
#scraperwiki.utils.urllibSetup   ()
#
##  This is for urllib2.urlopen() (and hance scraperwiki.scrape()) where
##  we can set explicit handlers.
##
#scraperwiki.utils.urllib2Setup \
#    (   urllib2.ProxyHandler ({'http':  httpProxy }),
#        urllib2.ProxyHandler ({'https': httpsProxy}),
#        urllib2.ProxyHandler ({'ftp':   ftpProxy  })
#    )
#
#if cache is not None :
#    scraperwiki.utils.allowCache (cache)
#
##  Pass the configuration to the datastore. At this stage no connection
##  is made; a connection will be made on demand if the scraper tries
##  to save anything.
##
#scraperwiki.datastore.DataStore (config)
#
#errfd = sys.stderr
#scraperwiki.console.setConsole  (sys.stderr)
#sys.stderr = sys.stdout
#
##  Set up a CPU time limit handler which simply throws a python
##  exception.
##
#def sigXCPU (signum, frame) :
#    raise Exception ("CPUTimeExceeded")
#
#signal.signal (signal.SIGXCPU, sigXCPU)
#
#def getTraceback (code) :
#
#    """
#    Get traceback information. Returns exception, traceback, the
#    scraper file in whch the error occured and the line number.
#
#    @return         : (exception, traceback, file, line)
#    """
#
#    if trace == 'text' :
#        import backtrace
#        return backtrace.backtrace ('text', code, context = 10)
#    if trace == 'html' :
#        import backtrace
#        return backtrace.backtrace ('html', code, context = 10)
#
#    import traceback
#    tb = [ \
#            string.replace (t, 'File "<string>"', 'Scraper')
#            for t in traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
#            if string.find (t, 'Controller.py') < 0
#          ]
#    return str(sys.exc_type), string.join(tb, ''), None, None
#
#def execute (code) :
#
#    try :
#        import imp
#        ostimes1   = os.times ()
#        cltime1    = time.time()
#        mod        = imp.new_module ('scraper')
#        exec code.rstrip() + "\n" in mod.__dict__
#        ostimes2   = os.times ()
#        cltime2    = time.time()
#        try    :
#            msg = '%d seconds elapsed, used %d CPU seconds' %  \
#                                    (   int(cltime2 - cltime1),
#                                        int(ostimes2[0] - ostimes1[0])
#                                    )
#            sys.stdout.write \
#                (   json.dumps \
#                    (   {   'message_type'  : 'console',
#                            'content'       : msg,
#                        }
#                    )   + '\n'
#                )
#            sys.stdout.flush ()
#        except :
#            pass
#        etext, trace, infile, atline = None, None, None, None
#    except Exception, e :
#        import errormapper
#        emsg = errormapper.mapException (e)
#        etext, trace, infile, atline = getTraceback (code)
#        errfd.write \
#            (   json.dumps \
#                (   {   'message_type'  : 'exception',
#                        'content'       : emsg,
#                        'content_long'  : trace,
#                        'filename'      : infile,
#                        'lineno'        : atline
#                    }
#                )   + '\n'
#            )
#        sys.stdout.flush ()
#
#execute (open(script).read())
require  $script  ;
?>
