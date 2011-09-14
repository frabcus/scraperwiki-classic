#!/usr/bin/env php
<?php

// set the include paths to scraperlibs from an environment variable (what can be done automatically for python and ruby)
foreach (split(':', getenv('PHPPATH')) as $dir)
    ini_set('include_path',  ini_get('include_path') . PATH_SEPARATOR . $dir) ;

$logfd = fopen("php://fd/3", "w") ;

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
        global $script;
		$etb = errorParserNoStack($error['type'], $error['message'], $error['file'], $error['line']); 
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
    $_GET[urldecode($QUERY_STRING_b[0])] = urldecode($QUERY_STRING_b[1]); 
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
    $etb = errorParserStack($errno, $errstr, $script); 
    scraperwiki::sw_dumpMessage($etb); 
    return true; 
}

set_error_handler("errorHandler", E_ALL & ~E_NOTICE);  // this is for errors, not exceptions (eg 1/0)

date_default_timezone_set('Europe/London');

// should parse and populate $_GET from getenv("QUERY_STRING") here

/*
    Can't get this to work - the exception raised inside the signal handler
    just makes the script fail silently. This isn't the end of the world,
    as higher level code at least now says it was SIGXCPU that killed it.

    Would be nice to get the stack trace though, like in Ruby/Python!

function sigXCPU($signum) {
    throw new Exception("ScraperWiki CPU time exceeded");
}
pcntl_signal(SIGXCPU, "sigXCPU"); */

try
{
    // works also as include or eval.  However no way to trap syntax errors
    require  $script  ;
}
catch(Exception $e)
{
    $etb = exceptionHandler($e, $script);
    //print_r($etb); 
    scraperwiki::sw_dumpMessage($etb); 
}
?>
