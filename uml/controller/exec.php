#!/usr/bin/php5
<?php

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
   $res  = curl_exec ($curl) ;

   curl_close ($curl) ;
   return   $res  ;
}


foreach (split (':', $path) as $dir)
    ini_set ('include_path',  ini_get('include_path') . PATH_SEPARATOR . $dir) ;

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
#try
{
   require  $script  ;
}
#catch (Exception $e)
#{
#   print "EXCEPTION\n" ;
#}

?>
