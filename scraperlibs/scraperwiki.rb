require 'json'
require	'uri'
require	'net/http'
require 'scraperwiki/datastore'
require 'scraperwiki/metadata'

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

end
