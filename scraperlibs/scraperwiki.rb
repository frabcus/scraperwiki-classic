require 'json'
require	'uri'
require	'net/http'
require 'scraperwiki/datastore'
require 'scraperwiki/metadata'
require 'scraperwiki/apiwrapper'

module ScraperWiki

    $cacheFor = 0

    def ScraperWiki.allowCache(cacheFor)
        $cacheFor = cacheFor
    end

    def ScraperWiki.dumpMessage(hash)
        $logfd.write(JSON.generate(hash) + "\n")
        $logfd.flush()
    end

    def ScraperWiki.save(unique_keys, data, date = nil, latlng = nil)
        res = SW_DataStore.create().save(unique_keys, data, date, latlng)
        if ! res[0]
            raise res[1]
        end
        ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => data})
    end

    def ScraperWiki.httpresponseheader(headerkey, headervalue)
        ScraperWiki.dumpMessage({'message_type' => 'httpresponseheader', 'headerkey' => headerkey, 'headervalue' => headervalue})
    end

    def ScraperWiki.scrape (url)
        uri  = URI.parse(url)
        data = Net::HTTP.get(uri)
        return data
    end

    def ScraperWiki.cache (enable = true)
        uri = URI.parse('http://127.0.0.1:9001/Option?runid=%s&webcache=%s' % [ ENV['RUNID'], enable ? $cacheFor : 0 ])
        Net::HTTP.get(uri)
    end

    def ScraperWiki.gb_postcode_to_latlng(postcode)
        if postcode == nil :
            return nil
        end
        ds  = SW_DataStore.create()
        res = ds.postcodeToLatLng(postcode)
        if ! res[0]
            ScraperWiki::dumpMessage({'message_type' => 'console', 'content' => 'Warning: %s: %s' % [res[1], postcode]})
            return nil
        end
        return res[1]
    end

    def ScraperWiki.get_metadata(metadata_name, default = nil)
        return SW_MetadataClient.create().get(metadata_name, default)
    end

    def ScraperWiki.save_metadata(metadata_name, value)
        ScraperWiki::dumpMessage({'message_type' => 'console', 'content' => 'Saving %s: %s' % [metadata_name, value]})
        return SW_MetadataClient.create().save(metadata_name, value)
    end



    def ScraperWiki.save(unique_keys, data, date = nil, latlng = nil)
        res = SW_DataStore.create().save(unique_keys, data, date, latlng)
        if ! res[0]
            raise res[1]
        end

        pdata = { }
        data.each_pair do |key, value|
            key = key.to_s
            if value == nil
                value  = ''
            else
                value = value.to_s
            end
            pdata[key] = value
        end
        ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => pdata})
    end


    def ScraperWiki.getKeys(name)
        return SW_APIWrapper.getKeys(name)
    end

    def ScraperWiki.getData(name, limit=-1, offset=0)
        SW_APIWrapper.getData(name, limit, offset)
    end
    
    def ScraperWiki.getDataByDate(name, start_date, end_date, limit=-1, offset=0)
        SW_APIWrapper.getDataByDate(name, start_date, end_date, limit, offset)
    end
    
    def ScraperWiki.getDataByLocation(name, lat, lng, limit=-1, offset=0)
        SW_APIWrapper.getDataByLocation(name, lat, lng, limit, offset)
    end
        
    def ScraperWiki.search(name, filterdict, limit=-1, offset=0)
        SW_APIWrapper.search(name, filterdict, limit, offset)
    end

end
