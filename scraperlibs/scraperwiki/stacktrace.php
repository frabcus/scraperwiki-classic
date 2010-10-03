<?php

function exceptionHandler($exception, $script) 
{
    // these are our templates
    $stackdump = array(); 
    $scriptlines = explode("\n", file_get_contents($script)); 
    foreach ($exception->getTrace() as $key => $stackPoint) 
    {
        $linenumber = $stackPoint["line"]-1; 
        $stackentry = array("linenumber" => $linenumber, "duplicates" => 1); 
        $stackentry["file"] = ($stackPoint["file"] == $script ? "<string>" : $stackPoint["file"]); 

        if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
            $stackentry["linetext"] = $scriptlines[$linenumber]; 

        if (array_key_exists("args", $stackPoint))
            $stackentry["furtherlinetext"] = "argsss ".print_r($stackPoint["args"], true); 

        $stackdump[] = $stackentry; 
    }
    
    $linenumber = $exception->getLine()-1; 
    $finalentry = array("linenumber" => $linenumber, "file" => $exception->getFile(), "duplicates" => 1); 
    $finalentry["file"] = ($exception->getFile() == $script ? "<string>" : $exception->getFile()); 
    if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
        $finalentry["linetext"] = $scriptlines[$linenumber]; 
    $finalentry["furtherlinetext"] = $exception->getMessage().count($scriptlines); 
    $stackdump[] = $finalentry; 
    
    return array('message_type' => 'exception', 'exceptiondescription' => $exception->getMessage(), "stackdump" => $stackdump); 
}

// error handler function (eg syntax errors and worse)
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
