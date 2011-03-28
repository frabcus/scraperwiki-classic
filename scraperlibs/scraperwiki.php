<?php

require_once   ('scraperwiki/datastore.php') ;
require_once   ('scraperwiki/metadata.php' ) ;
require_once   ('scraperwiki/stacktrace.php' ) ;
require_once   ('scraperwiki/apiwrapper.php' ) ;

class scraperwiki
{
   private static $m_cacheFor = 0 ;

   static function sw_allowCache ($cacheFor)
   {
      self::$m_cacheFor = $cacheFor ;
   }

   static function sw_dumpMessage ($dict)
   {
      global $logfd ;
      fwrite ($logfd, json_encode ($dict) . "\n") ;
   }

   static function sw_logScrapedURL ($url, $length)
   {
       scraperwiki::sw_dumpMessage
           /* seexception(errmap):
        mess = errmap["error"]
        for k, v in errmap.items():
        if k != "error" {
            mess = "%s; %s:%s" % (mess, k, v)

        if re.match('sqlite3.Error: no such table:', mess):
        return NoSuchTableSqliteError(mess)
    return SqliteError(mess)


def save_sqlite(unique_keys, data, table_name="swdata", verbose=2):
    ds = DataStore(None)
    result = ds.save_sqlite(unique_keys, data, table_name)
    if "error" in result:
        raise databaseexception(result)
            */

         (  array
            (  'message_type' => 'sources',
               'url'          => $url,
               'content'      => sprintf ("%d bytes from %s", $length, $url)
         )  )  ;
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
      $olddatastoreitemcount = $ds->request(array('item_count')); 
      if ($olddatastoreitemcount[1] != 0)
      {
        $result = $ds->save($unique_keys, $data, $date, $latlng);
        if (! $result[0])
            throw new Exception ($result[1]) ;
    
        scraperwiki::sw_dumpMessage (array('message_type' => 'data', 'content' => $data)) ;
      }

      $ldata = $data.copy();   // what's the function?
      if (!is_null($date))
         $ldata["date"] = $date; 
      if (!is_null($latlng))
      {
         $ldata["latlng_lat"] = $latlng[0]; 
         $ldata["latlng_lng"] = $latlng[1]; 
      }
      return scraperwiki::save_sqlite($unique_keys, $ldata); 
   }

   static function sqlitecommand($command, $val1 = null, $val2 = null)
   {
      $ds = SW_DataStoreClass::create();
      $result = $ds->request(array('sqlitecommand', $command, $val1, $val2));
      if (property_exists($result, 'error'))
         throw new Exception ($result->error) ;
      scraperwiki::sw_dumpMessage (array('message_type'=>'sqlitecall', 'command'=>$command, 'val1'=>$val1, 'val2'=>$val2));
      return $result; 
   }

   static function save_sqlite($unique_keys, $data, $table_name="swdata", $verbose=2)
   {
      $ds = SW_DataStoreClass::create();
      $result = $ds->request(array('save_sqlite', $unique_keys, $data, $table_name)); 
      if (property_exists($result, 'error'))
         throw new Exception ($result->error) ;
      scraperwiki::sw_dumpMessage(array('message_type'=>'data', 'content'=>$data));
      return $result; 
   }

   static function select($val1, $val2=null)
   {
      $result = scraperwiki::sqlitecommand("execute", "select ".$val1, $val2); 
      //http://rosettacode.org/wiki/Hash_from_two_arrays
      $res = array(); 
      foreach ($result->data as $i => $row)
         array_push($res, array_combine($result->keys, $row)); 
      return $res; 
   }

   static function attach($name, $asname=null)
   {
      scraperwiki::sqlitecommand("attach", $name, $asname); 
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
      $ds = SW_DataStoreClass::create () ;
      $result = $ds->request(array('sqlitecommand', "execute", "select value_blob, type from swvariables where name=?", array($name)));
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
      if (is_null($postcode))
         return null ;

      $ds      = SW_DataStoreClass::create () ;

      $result  = $ds->postcodeToLatLng ($postcode) ;
      if (! $result[0])
      {
         scraperwiki::sw_dumpMessage
            (  array
                  (  'message_type' => 'console',
                     'content'      => 'Warning: ' + sprintf('%s: %s', $result[1], $postcode)
                  )
            )  ;
        return null  ;
      }

      return $result[1] ;
   }

   static function scrape ($url)
   {
      $curl = curl_init ($url ) ;
      curl_setopt ($curl, CURLOPT_RETURNTRANSFER, true) ;
      $res  = curl_exec ($curl) ;
      curl_close ($curl) ;
      return   $res;
   }

   static function cache ($enable = true)
   {
      file_get_html
         (  sprintf
            (  "http://127.0.0.1:9001/Option?runid=%s&webcache=%s",
               getenv('RUNID'),
               $enable ? self::$m_cacheFor : 0
         )  )  ;
   }


   // the meta functions weren't being used to any extent in PHP anyway
   static function get_metadata($metadata_name, $default = null)
   {
      return scraperwiki::get_var($metadata_name, $default); 
      //return SW_MetadataClient::create()->get($metadata_name);
   }

   static function save_metadata($metadata_name, $value)
   {
      return scraperwiki::save_var($metadata_name, $value); 
      //return SW_MetadataClient::create()->save($metadata_name, $value);
   }


    static function getInfo($name) {
        return SW_APIWrapperClass::getInfo($name); 
    }

    static function getKeys($name) {
        return SW_APIWrapperClass::getKeys($name); 
    }
    static function getData($name, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::getData($name, $limit, $offset); 
    }

    static function getDataByDate($name, $start_date, $end_date, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::getDataByDate($name, $start_date, $end_date, $limit, $offset); 
    }
    
    static function getDataByLocation($name, $lat, $lng, $limit= -1, $offset= 0) { 
        return SW_APIWrapperClass::getDataByLocation($name, $lat, $lng, $limit, $offset); 
    }
        
    static function search($name, $filterdict, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::search($name, $filterdict, $limit, $offset);
    }
}

?>
