<?php
class MetadataClient
{   
    private static $instance;

    public static function create()
    {
        if (!isset(self::$instance))
        {
            self::$instance = new MetadataClient();
        }

        return self::$instance;
    }

    private function get_url($metadata_name)
    {
        return sprintf("http://%s/scrapers/metadata_api/%s/%s/", getenv("metadata_host"), getenv("SCRAPER_GUID"), urlencode($metadata_name));
    }
    
    private function get_metadata($metadata_name)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('x-scraperid: ' . getenv("SCRAPER_GUID"))); 
        curl_setopt($ch, CURLOPT_URL, $this->get_url($metadata_name));
        curl_setopt ($ch, CURLOPT_RETURNTRANSFER, true);
        $res = curl_exec($ch);
        curl_close($ch);

        if($res)
        {
            return json_decode($res);
        }
        else
        {
            return null;
        }
    }
    
    public function get($metadata_name, $default=null)
    {
        $metadata = $this->get_metadata($metadata_name);
        if($metadata)
        {
            return json_decode($metadata->{"value"});
        }
        else
        {
            return $default;
        }
    }    

    
    public function get_run_id($metdata_name)
    {
        $metadata = $this->get_metadata($metadata_name);
        if($metadata)
        {
            return json_decode($metadata->{"run_id"});
        }
        else
        {
            return null;
        }
    }
    
    public function save($metadata_name, $value)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('x-scraperid: ' . getenv("SCRAPER_GUID"))); 
        curl_setopt($ch, CURLOPT_URL, $this->get_url($metadata_name));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);

        if($this->get($metadata_name))
        {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
        }
        else
        {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
        }

        curl_setopt($ch, CURLOPT_POSTFIELDS, sprintf("run_id=%s&value=%s", getenv("RUNID"), $value));
        
        $res = curl_exec($ch);
        curl_close($ch);
        return $res;
    }        
}
?>
