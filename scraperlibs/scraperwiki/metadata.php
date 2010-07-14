<?php
class SW_MetadataClient
{   
    private static $instance;

    public static function create()
    {
        if (!isset(self::$instance))
        {
            self::$instance = new SW_MetadataClient();
        }

        return self::$instance;
    }

    function __construct()
    {
        if(!getenv("SCRAPER_GUID"))
        {
            $this->metadata_local = Array("title" => "Untitled Scraper", "CPU limit" => "100");
        }

    }

    private function get_url($metadata_name)
    {
        return sprintf("http://%s/scrapers/metadata_api/%s/%s/", getenv("metadata_host"), getenv("SCRAPER_GUID"), urlencode($metadata_name));
    }
    
    private function get_metadata($metadata_name)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $this->get_url($metadata_name));
        curl_setopt ($ch, CURLOPT_RETURNTRANSFER, true);
        $res = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if($status == 200)
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
        if(!getenv("SCRAPER_GUID"))
        {
            $value = $this->metadata_local[$metadata_name];
            if($value == null)
            {
                return $default;
            }
            return $value;
        }

        $metadata = $this->get_metadata($metadata_name);
        if($metadata)
        {
            return json_decode($metadata->value);
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
            return json_decode($metadata->run_id);
        }
        else
        {
            return null;
        }
    }
    
    public function save($metadata_name, $value)
    {
        if(!getenv("SCRAPER_GUID"))
        {
            print 'The scraper has not been saved yet. Metadata will not be persisted between runs\n';
            $this->metadata_local[$metadata_name] = $value;
        }

        $ch = curl_init();
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

        curl_setopt($ch, CURLOPT_POSTFIELDS, sprintf("run_id=%s&value=%s", getenv("RUNID"), json_encode($value)));
        
        $res = curl_exec($ch);
        curl_close($ch);
        return $res;
    }
}
?>
