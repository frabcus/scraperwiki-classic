#!/usr/bin/env php
<?php

// set the include paths to scraperlibs from an environment variable (what can be done automatically for python and ruby)
foreach (split(':', getenv('PHPPATH')) as $dir)
    ini_set('include_path',  ini_get('include_path') . PATH_SEPARATOR . $dir) ;

$logfd = STDOUT; // fopen("php://fd/3", "w") ;
fclose(STDERR);
$STDERR = fopen('php://stdout', 'w');


require_once 'scraperwiki.php';
require_once 'scraperwiki/datastore.php';
require_once 'scraperwiki/stacktrace.php';

ob_implicit_flush(true);

$script = null;
$datastore = null;
$scrapername = null; 
$runid = null; 
for ($idx = 1; $idx < count($argv); $idx += 1)
{
   $arg  = $argv[$idx] ;

   if (substr($arg, 0, 5) == '--qs=')
   {
      $qs = substr($arg,  5);
	  if ( strlen($qs) > 0 ) {
		putenv("QUERY_STRING", $qs);
		putenv("URLQUERY", $qs);
	  }
   }

   if (substr ($arg, 0,  9) == '--script=')
      $script = substr ($arg, 9);
   if (substr ($arg, 0, 5) == '--ds=')
      $datastore = substr($arg, 5);
   if (substr ($arg, 0, 14) == '--scrapername=')
      $scrapername = substr($arg, 14);
   if (substr ($arg, 0, 8) == '--runid=')
      $runid = substr($arg, 8);
   if (substr($arg, 0, 6) == '--gid=')
   {
      $gid = substr($arg,  6);
      posix_setgid($gid);
      posix_setegid($gid);
   }
   if (substr ($arg, 0, 6) == '--uid=')
   {
      $uid = substr($arg, 6);
      posix_setuid($uid);
      posix_seteuid($uid);
   }
}


function shutdown(){
    $isError = false;

    if ($error = error_get_last()){
        switch($error['type']){
			case E_ERROR:
            case E_CORE_ERROR:
            case E_COMPILE_ERROR:
            case E_USER_ERROR:	
            case E_PARSE:
                $isError = true;
                break;
    }
                                             }
    if ($isError){
		$etb = errorParser($error['type'], $error['message'], $error['file'], $error['line'], '/home/scriptrunner/script.php'); 
    	scraperwiki::sw_dumpMessage($etb); 	
    }
}
register_shutdown_function('shutdown');



// make the $_GET array
$QUERY_STRING = getenv("QUERY_STRING");
$QUERY_STRING_a = explode('&', $QUERY_STRING);
$_GET = array(); 
for ($i = 0; $i < count($QUERY_STRING_a); $i++)
{
    $QUERY_STRING_b = split('=', $QUERY_STRING_a[$i]);
	if ( count( $QUERY_STRING_b ) > 1 ) {
    	$_GET[urldecode($QUERY_STRING_b[0])] = urldecode($QUERY_STRING_b[1]); 
	}
}


$dsinfo = split (':', $datastore) ;
SW_DataStoreClass::create ($dsinfo[0], $dsinfo[1], $scrapername, $runid) ;

// the following might be the only way to intercept syntax errors
//$errors = array(); 
//parsekit_compile_file($script, $errors); 

// refer to http://php.net/manual/en/function.set-error-handler.php
function errorHandler($errno, $errstr, $errfile, $errline)
{
    global $script; 
    $etb = errorParser($errno, $errstr, $errfile, $errline, $script); 
    scraperwiki::sw_dumpMessage($etb); 
    return true; 
}

set_error_handler("errorHandler", E_ALL & ~E_NOTICE);  // this is for errors, not exceptions (eg 1/0)
set_time_limit(80); 

date_default_timezone_set('Europe/London');

try
{
    // works also as include or eval.  However no way to trap syntax errors
    require  $script;
}
catch(Exception $e)
{
    $etb = exceptionHandler($e, $script);
    print_r($etb); 
    scraperwiki::sw_dumpMessage($etb); 
}
?>
