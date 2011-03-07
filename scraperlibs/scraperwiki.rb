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

    def ScraperWiki.httpresponseheader(headerkey, headervalue)
        ScraperWiki.dumpMessage({'message_type' => 'httpresponseheader', 'headerkey' => headerkey, 'headervalue' => headervalue})
    end

    def ScraperWiki.scrape (url, params = nil)
        uri  = URI.parse(url)
        if params.nil?
            data = Net::HTTP.get(uri)
        else
            if uri.path = ''
                uri.path = '/' # must post to a path
            end
            data = Net::HTTP.post_form(uri, params)
        end
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

        pdata = { }
        data.each_pair do |key, value|
            key = key.to_s[0,50]
            if value == nil
                value  = ''
            else
                value = value.to_s[0,50]
            end
            pdata[key] = value
        end
        ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => pdata})
    end

    def ScraperWiki.sqlitecommand(command, val1=nil, val2=nil, verbose=2)
        ds = SW_DataStore.create()
        res = ds.request(['sqlitecommand', command, val1, val2])
        if res["error"]
            raise res["error"]
        end
        if verbose:
            ScraperWiki.dumpMessage({'message_type'=>'sqlitecall', 'command'=>command, 'val1'=>res, 'val2'=>res})
        end
    end

    def ScraperWiki.save_sqlite(unique_keys, data, table_name="swdata", commit=true, verbose=2)
        for key in unique_keys
            if !data.include?(key)
                raise 'unique_keys must be a subset of data'
            end
        end

        jdata = { }
        data.each_pair do |key, value|
            if not key:
                raise 'key must not be blank'
            end
            if key.class != String
                raise 'key must be string type'
            end

            if !/[a-zA-Z0-9_\- ]+$/.match(key)
                raise 'key must be simple text'+key
            end
            
            if ![Fixnum, Float, String, TrueClass, FalseClass, NilClass].include?(value)
                value = value.to_s
            end
            jdata[key] = value
        end

        ds = SW_DataStore.create()
        res = ds.request(['save_sqlite', unique_keys, jdata, table_name])
        if res["error"]
            raise res["error"]
        end
        if commit
            res = ds.request(['sqlitecommand', 'commit', nil, nil]);
        end

        pdata = { }
        jdata.each_pair do |key, value|
            key = key.to_s[0,50]
            if value == nil
                value  = ''
            else
                value = value.to_s[0,50]
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
