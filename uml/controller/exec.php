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
$uid         = undef ;
$gid         = undef ;

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
   if (substr ($arg, 0, 6) == '--uid='       )
   {
      $uid        = substr ($arg,  6) ;
      continue    ;
   }
   if (substr ($arg, 0, 6) == '--gid='       )
   {
      $gid        = substr ($arg,  6) ;
      continue    ;
   }

   print "usage: " . $argv[0] . $USAGE . "\n" ;
   exit  (1) ;
}

// need to comment out for local version
$logfd = fopen("/proc/self/fd/3", "w") ;
if (!is_null($gid))
{
   posix_setgid  ($gid) ;
   posix_setegid ($gid) ;
}
if (!is_null($uid))
{
   posix_setuid  ($uid) ;
   posix_seteuid ($uid) ;
}

foreach (split (':', $path) as $dir)
    ini_set ('include_path',  ini_get('include_path') . PATH_SEPARATOR . $dir) ;

require_once   'scraperwiki/datastore.php' ;
require_once   'scraperwiki.php'           ;

$dsinfo = split (':', $datastore) ;
SW_DataStoreClass::create ($dsinfo[0], $dsinfo[1]) ;

if (!is_null ($cache))
   scraperwiki::sw_allowCache ($cache) ;

#
#def sigXCPU (signum, frame) :
#    raise Exception ("CPUTimeExceeded")
#
#signal.signal (signal.SIGXCPU, sigXCPU)
#
try
{
    require  $script  ;
}
catch(Exception $e)
{
    $etb = exceptionHandler($e);
    print_r($etb); 
    #echo $etb;
    scraperwiki::sw_dumpMessage($etb); 
}
?>
