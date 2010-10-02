<?php

function exceptionHandler($exception) 
{
    // these are our templates
    $stackdump = array(); 
    foreach ($exception->getTrace() as $key => $stackPoint) 
    {
        $stackentry = array("linenumber" => $stackPoint["line"], "file" => $stackPoint["file"], "duplicates" => 1); 
        $stackentry["linetext"] = "put code line here"; 
        $stackentry["furtherlinetext"] = "argsss ".print_r($stackPoint["args"], true); 
        $stackdump[] = $stackentry; 
    }
    
    $finalentry = array("linenumber" => $exception->getLine(), "file" => $exception->getFile(), "duplicates" => 1); 
    $finalentry["linetext"] = $exception->getMessage(); 
    $stackdump[] = $stackentry; 
    
    return array('message_type' => 'exception', 'exceptiondescription' => $exception->getMessage(), "stackdump" => $stackdump); 
}

// error handler function
function myErrorHandler($errno, $errstr, $errfile, $errline)
{
echo "hihihi $errno, $errstr, $errfile, $errline ------======="; 

    if (!(error_reporting() & $errno)) {
        // This error code is not included in error_reporting
        return;
    }

    switch ($errno) {
    case E_USER_ERROR:
        echo "<b>My ERROR</b> [$errno] $errstr<br />\n";
        echo "  Fatal error on line $errline in file $errfile";
        echo ", PHP " . PHP_VERSION . " (" . PHP_OS . ")<br />\n";
        echo "Aborting...<br />\n";
        exit(1);
        break;

    case E_USER_WARNING:
        echo "<b>My WARNING</b> [$errno] $errstr<br />\n";
        break;

    case E_USER_NOTICE:
        echo "<b>My NOTICE</b> [$errno] $errstr<br />\n";
        break;

    default:
        echo "Unknown error type: [$errno] $errstr<br />\n";
        break;
    }

    /* Don't execute PHP internal error handler */
    return true;
}

set_error_handler("myErrorHandler");
error_reporting(E_ALL);

?>
