require	'uri'
require	'net/http'
require 'json'

$M_MD	= nil

class SW_MetadataClient

    def initialize()
        if ! ENV["SCRAPER_GUID"]
            @metadata_local = { "title" => "Untitled Scraper", "CPU limit" => "100" }
        end
    end

    def get_url(metadata_name)
        return "http://%s/scrapers/metadata_api/%s/%s/" % [ENV["metadata_host"], ENV["SCRAPER_GUID"], urlencode(metadata_name)]
    end
    
    def get_metadata(metadata_name)
        uri = URI.parse(get_url(metadata_name))
        res = Net::HTTP.get(uri)
        return JSON.parse(res)
    end
    
    def get(metadata_name, default = nil)
        if ENV["SCRAPER_GUID"]
            value = @metadata_local[metadata_name]
            if value == nil
                return default
            end
            return value
        end
        metadata = get_metadata(metadata_name)
        if ! metadata
            return default
        end
        return JSON.parse(metadata['value'])
    end
    
    def save(metadata_name, value)
        if ! ENV["SCRAPER_GUID"]
             print 'The scraper has not been saved yet. Metadata will not be persisted between runs\n'
             @metadata_local[metadata_name] = value
             return nil
        end
        return nil
    end
#
#        $ch = curl_init();
#        curl_setopt($ch, CURLOPT_URL, $this->get_url($metadata_name));
#        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
#
#        if($this->get($metadata_name))
#        {
#            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
#        }
#        else
#        {
#            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
#        }
#
#        curl_setopt($ch, CURLOPT_POSTFIELDS, sprintf("run_id=%s&value=%s", getenv("RUNID"), json_encode($value)));
#        
#        $res = curl_exec($ch);
#        curl_close($ch);
#        return $res;
#    }

    def SW_MetadataClient.create()
        if ! $M_MD
            $M_MD = SW_MetadataClient.new()
        end
        return $M_MD
    end
end
