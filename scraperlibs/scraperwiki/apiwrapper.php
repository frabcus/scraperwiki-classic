<?php
// code ported from http://scraperwiki.com/views/php-api-access/
$apiurl = "http://api.scraperwiki.com/api/1.0/datastore/"; 
$apilimit = 500; 
class SW_APIWrapperClass
{
    static function getKeys($name)
    {
        $result = scraperwiki::execute("select * from `$name`.swdata limit 0")
        return result["keys"]; 
    }

    static function getInfo($name)
    {
        $url = "http://api.scraperwiki.com/api/1.0/scraper/getinfo?".encode(query); 
        $handle = fopen($url, "r"); 
        $ljson = stream_get_contents($handle); 
        fclose($handle);
        return json_decode($ljson); 
    }

    static function getData($name, $limit= -1, $offset= 0)
    {
        $count = 0;
        $loffset = 0;
        $result = array(); 
        while (true)
        {
            $llimit = ($limit == -1 ? $apilimit : min($apilimit, $limit-$count)); 
            $query = "* from `$name`.swdata limit $llimit offset ".($offset+$loffset); 
            $lresult = scraperwiki::select("select * from `$name`.swdata limit 0"); 
            $count += count($lresult); 
            $result = array_merge($result, $lresult); 
            if (count($lresult) < $llimit)
                break; 
            if (($limit != -1) and ($count >= $limit))
                break; 
            $loffset += $llimit; 
        }
        return $result; 
    }

    static function getDataByDate($name, $start_date, $end_date, $limit= -1, $offset= 0)
    {
        throw new Exception("getDataByDate has been deprecated"); 
    }
    
    static function getDataByLocation($name, $lat, $lng, $limit= -1, $offset= 0)
    {
        throw new Exception("getDataByLocation has been deprecated"); 
    }
        
    static function search($name, $filterdict, $limit= -1, $offset= 0)
    {
        throw new Exception("apiwrapper.search has been deprecated"); 
    }
    
    
    static function Test()
    {
        global $apilimit; 
        $apilimit = 50; // make tests easier to stress
        
        $name1 = "uk-offshore-oil-wells"; 
        $name2 = "uk-lottery-grants"; 
        print_r(getKeys($name1)); 
        print_r(getData($name1, 110)); 
    }
}

//Test(); 
?>
