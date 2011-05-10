<?php

require_once   ('scraperwiki/datastore.php') ;
require_once   ('scraperwiki/stacktrace.php' ) ;

class scraperwiki
{
   private static $attachlist = array();

   static function sw_dumpMessage($dict)
   {
      global $logfd ;
      if ($logfd)
          fwrite ($logfd, json_encode ($dict) . "\n") ;
   }

   static function httpresponseheader ($headerkey, $headervalue)
   {
       scraperwiki::sw_dumpMessage
         (  array
            (  'message_type' => 'httpresponseheader',
               'headerkey'    => $headerkey,
               'headervalue'  => $headervalue
         )  )  ;
   }

   static function save($unique_keys, $data, $date = null, $latlng = null)
   {
      $ds = SW_DataStoreClass::create() ;
      $ldata = $data;   
      if (!is_null($date))
         $ldata["date"] = $date; 
      if (!is_null($latlng))
      {
         $ldata["latlng_lat"] = $latlng[0]; 
         $ldata["latlng_lng"] = $latlng[1]; 
      }
      return scraperwiki::save_sqlite($unique_keys, $ldata); 
   }

   static function sqlitecommand($command, $val1=null, $val2=null, $verbose=1)
   {
      $ds = SW_DataStoreClass::create();
      $result = $ds->request(array('maincommand'=>'sqlitecommand', 'command'=>$command, 'val1'=>$val1, 'val2'=>$val2));
      if (property_exists($result, 'error'))
         throw new Exception ($result->error);
      if ($verbose != 0)
         scraperwiki::sw_dumpMessage(array('message_type'=>'sqlitecall', 'command'=>$command, 'val1'=>$val1, 'val2'=>$val2));
      return $result; 
   }

   static function unicode_truncate($val, $n)
   {
      if ($val == null)
         $val = ""; 
      return substr($val, 0, $n); //need to do more?
   }

   static function save_sqlite($unique_keys, $data, $table_name="swdata", $verbose=2)
   {
      $ds = SW_DataStoreClass::create();
      $result = $ds->request(array('maincommand'=>'save_sqlite', 'unique_keys'=>$unique_keys, 'data'=>$data, 'swdatatblname'=>$table_name)); 
      if (property_exists($result, 'error'))
         throw new Exception ($result->error);

      if ($verbose == 2)
      {
         if (array_key_exists(0, $data))
            $sdata = $data[0]; 
         else
            $sdata = $data;
         $pdata = array(); 
         foreach ($sdata as $key=>$value)
            $pdata[scraperwiki::unicode_truncate($key, 50)] = scraperwiki::unicode_truncate($value, 50); 
         if (array_key_exists(0, $data) && (count($data) >= 2))
            $pdata["number_records"] = "Number Records: ".count($data); 
         scraperwiki::sw_dumpMessage(array('message_type'=>'data', 'content'=>$pdata));
      }
      return $result; 
   }

   static function select($val1, $val2=null)
   {
      $result = scraperwiki::sqlitecommand("execute", "select ".$val1, $val2); 

          // see http://rosettacode.org/wiki/Hash_from_two_arrays
      $res = array(); 
      foreach ($result->data as $i => $row)
         array_push($res, array_combine($result->keys, $row)); 
      return $res; 
   }

   static function attach($name, $asname=null)
   {
      $attachlist.push(array("name"=>$name, "asname"=>$asname)); 
      return scraperwiki::sqlitecommand("attach", $name, $asname); 
   }
   static function sqlitecommit()
   {
      return scraperwiki::sqlitecommand("commit"); 
   }
   static function sqliteexecute($val1, $val2=null, $verbose=1)
   {
      return scraperwiki::sqlitecommand("execute", $val1, $val2, $verbose); 
   }

   static function show_tables($dbname=null)
   {
      $name = "sqlite_master"; 
      if ($dbname != null)
          $name = "`$dbname`.sqlite_master"; 
      $result = scraperwiki::sqlitecommand("execute", "select tbl_name, sql from $name where type='table'"); 
      $res = array(); 
      foreach ($result->data as $i=>$row)
         $res[$row[0]] = $row[1]; 
      return $res; 
   }

   static function table_info($name)
   {
      $sname = explode(".", $name); 
      if (count($sname) == 2)
          $result = scraperwiki::sqlitecommand("execute", "PRAGMA ".$sname[0].".table_info(`".$sname[1]."`)"); 
      else
          $result = scraperwiki::sqlitecommand("execute", "PRAGMA table_info(`".$name."`)"); 
      $res = array(); 
      foreach ($result->data as $i => $row)
         array_push($res, array_combine($result->keys, $row)); 
      return $res; 
   }

   static function save_var($name, $value)
   {
      if (is_int($value))
         $jvalue = $value; 
      else if (is_double($value))
         $jvalue = $value; 
      else
         $jvalue = json_encode($value); 
      $data = array("name"=>$name, "value_blob"=>$jvalue, "type"=>gettype($value)); 
      scraperwiki::save_sqlite(array("name"), $data, "swvariables"); 
   }

   static function get_var($name, $default=None)
   {
      $ds = SW_DataStoreClass::create ();
      $result = scraperwiki::sqlitecommand("execute", "select value_blob, type from swvariables where name=?", array($name)); 
      if (property_exists($result, 'error'))
      {
         if (substr($result->error, 0, 29) == 'sqlite3.Error: no such table:')
            return $default;
         throw new Exception($result->error) ;
      }
      $data = $result->data; 
      if (count($data) == 0)
         return $default; 
      return $data[0][0]; 
   }


   static function gb_postcode_to_latlng ($postcode)
   {
       $url = "http://scraperwikiviews.com/run/uk_postcode_lookup/?postcode=".urlencode($postcode); 
       $sres = scraperwiki::scrape($url); 
       $jres = json_decode($sres, true); 
       if ($jres["lat"] && $jres["lng"])
            return array($jres["lat"], $jres["lng"]); 
       return null; 
   }

   static function scrape($url)
   {
      $curl = curl_init ($url ) ;
      curl_setopt ($curl, CURLOPT_RETURNTRANSFER, true) ;
      $res  = curl_exec ($curl) ;
      curl_close ($curl) ;
      return   $res;
   }

   // the meta functions weren't being used to any extent in PHP anyway
   static function get_metadata($metadata_name, $default = null)
   {
      return scraperwiki::get_var($metadata_name, $default); 
   }

   static function save_metadata($metadata_name, $value)
   {
      return scraperwiki::save_var($metadata_name, $value); 
   }


    static function getInfo($name) {
        $url = "http://api.scraperwiki.com/api/1.0/scraper/getinfo?name=".urlencode($name); 
        $handle = fopen($url, "r"); 
        $ljson = stream_get_contents($handle); 
        fclose($handle);
        return json_decode($ljson); 
    }

    static function getKeys($name) {
        throw new Exception("getKeys has been deprecated"); 
    }
    static function getData($name, $limit= -1, $offset= 0) {
        throw new Exception("getData has been deprecated"); 
    }

    static function getDataByDate($name, $start_date, $end_date, $limit= -1, $offset= 0) {
        throw new Exception("getDataByDate has been deprecated"); 
    }
    
    static function getDataByLocation($name, $lat, $lng, $limit= -1, $offset= 0) { 
        throw new Exception("getDataByLocation has been deprecated"); 
    }
        
    static function search($name, $filterdict, $limit= -1, $offset= 0) {
        throw new Exception("apiwrapper.search has been deprecated"); 
    }
}

?>
