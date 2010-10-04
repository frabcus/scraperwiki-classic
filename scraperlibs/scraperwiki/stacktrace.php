<?php

function exceptionHandler($exception, $script) 
{
    $stackdump = array(); 
    $scriptlines = explode("\n", file_get_contents($script)); 
    $trace = $exception->getTrace(); 
    for ($i = count($trace) - 2; $i >= 0; $i--)
    {
        $stackPoint = $trace[$i]; 
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
    $finalentry = array("linenumber" => $linenumber, "duplicates" => 1); 
    $finalentry["file"] = ($exception->getFile() == $script ? "<string>" : $exception->getFile()); 
    if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
        $finalentry["linetext"] = $scriptlines[$linenumber]; 
    $finalentry["furtherlinetext"] = $exception->getMessage().count($scriptlines); 
    $stackdump[] = $finalentry; 
    
    return array('message_type' => 'exception', 'exceptiondescription' => $exception->getMessage(), "stackdump" => $stackdump); 
}

function errorParser($errno, $errstr, $errfile, $errline, $script)
{
    $stackdump = array(); 
    $scriptlines = explode("\n", file_get_contents($script)); 
    $errorentry = array("linenumber" => $errline, "duplicates" => 1); 
    $errorentry["file"] = ($errfile == $script ? "<string>" : $errfile); 
    if (($errline >= 0) && ($errline < count($scriptlines)))
        $errorentry["linetext"] = $scriptlines[$errline]; 
    $errcode = ($errno == E_USER_ERROR ? "E_USER_ERROR" : ($errno == E_USER_WARNING ? "E_USER_WARNING" : "E_USER_NOTICE")); 

    $stackdump[] = $errorentry; 
    return array('message_type' => 'exception', 'exceptiondescription' => $errstr."  ".$errcode, "stackdump" => $stackdump); 
}


?>
