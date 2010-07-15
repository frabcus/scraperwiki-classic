<?php

require_once   ('scraperwiki/datastore.php') ;
require_once   ('scraperwiki/metadata.php' ) ;

class scraperwiki
{
   private static $m_cacheFor = 0 ;

   function sw_allowCache ($cacheFor)
   {
      self::$m_cacheFor = $cacheFor ;
   }

   function sw_dumpMessage ($dict)
   {
      global $logfd ;
      fwrite ($logfd, json_encode ($dict) . "\n") ;
   }

   function sw_logScrapedURL ($url, $length)
   {
       scraperwiki::sw_dumpMessage
         (  array
            (  'message_type' => 'sources',
               'url'          => $url,
               'content'      => sprintf ("%d bytes from %s", $length, $url)
         )  )  ;
   }

   function save ($unique_keys, $data, $date = null, $latlng = null)
   {
      $ds      = SW_DataStoreClass::create () ;
   
      $result  = $ds->save ($unique_keys, $data, $date = null, $latlng = null) ;
      if (! $result[0])
         throw new Exception ($result[1]) ;
   
      scraperwiki::sw_dumpMessage (array('message_type' => 'data', 'content' => $data)) ;
   }

   function gb_postcode_to_latlng ($postcode)
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

   function scrape ($url)
   {
      $curl = curl_init ($url ) ;
      curl_setopt ($curl, CURLOPT_RETURNTRANSFER, true) ;
      $res  = curl_exec ($curl) ;
      curl_close ($curl) ;
      return   $res  ;
   }

   function cache ($enable = true)
   {
      file_get_html
         (  sprintf
            (  "http://127.0.0.1:9001/Option?runid=%s&webcache=%s",
               getenv('RUNID'),
               $enable ? self::$m_cacheFor : 0
         )  )  ;
   }

   function get_metadata($metadata_name, $default = null)
   {
      return SW_MetadataClient::create()->get($metadata_name);
   }

   function save_metadata($metadata_name, $value)
   {
      print "Saving " . $metadata_name . ": " . $value . "\n";
      return SW_MetadataClient::create()->save($metadata_name, $value);
   }
}
?>
