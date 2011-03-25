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

    def ScraperWiki._scrape_uri_with_redirect(uri, limit = 10)
      # You should choose better exception.
      raise ArgumentError, 'HTTP redirect too deep' if limit == 0

      response = Net::HTTP.get_response(uri)
      case response
      when Net::HTTPSuccess     then response
      when Net::HTTPRedirection then _scrape_uri_with_redirect(uri.merge(response['location']), limit - 1)
      else
        response.error!
      end
    end

    def ScraperWiki.scrape (url, params = nil)
        uri  = URI.parse(url)
        if params.nil?
            data = ScraperWiki._scrape_uri_with_redirect(uri).body
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
        res = ds.request(['postcodetolatlng', postcode])
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

    def ScraperWiki._unicode_truncate(string, size)
        # Stops 2 byte unicode characters from being chopped in half which kills JSON serializer
        string.scan(/./u)[0,size].join
    end

    def ScraperWiki.save(unique_keys, data, date = nil, latlng = nil)
        if unique_keys != nil && !unique_keys.kind_of?(Array)
            raise 'unique_keys must be nil or an array'
        end

        ds = SW_DataStore.create()
        js_data = ds.mangleflattendict(scraper_data)
        uunique_keys = ds.mangleflattenkeys(unique_keys)
        res = ds.request(['save', uunique_keys, js_data, date, latlng])

        raise res[1] if not res[0]

        pdata = { }
        data.each_pair do |key, value|
            key = ScraperWiki._unicode_truncate(key.to_s, 50)
            if value == nil
                value  = ''
            else
                value = ScraperWiki._unicode_truncate(value.to_s, 50)
            end
            pdata[key] = value
        end
        ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => pdata})
    end

    class SqliteException < RuntimeError
    end

    class NoSuchTableSqliteException < SqliteException
    end

    def ScraperWiki.sqlitecommand(command, val1=nil, val2=nil, verbose=2)
        ds = SW_DataStore.create()
        res = ds.request(['sqlitecommand', command, val1, val2])
        if res["error"]
            if /sqlite3.Error: no such table:/.match(res["error"])
                raise NoSuchTableSqliteException.new(res["error"])
            end
            raise SqliteException.new(res["error"])
        end
        if verbose:
            ScraperWiki.dumpMessage({'message_type'=>'sqlitecall', 'command'=>command, 'val1'=>res, 'val2'=>res})
        end
        return res
    end

            # this ought to be a local function
    def ScraperWiki.convdata(unique_keys, scraper_data)
        puts unique_keys
        puts scraper_data
        if unique_keys:
            for key in unique_keys
                if !scraper_data.include?(key)
                    return { "error" => 'unique_keys must be a subset of data', "bad_key" => key }
                end
                if scraper_data[key] == nil:
                    return { "error" => 'unique_key value should not be None', "bad_key" => key }
                end
            end
        end

        jdata = { }
        scraper_data.each_pair do |key, value|
            if not key
                return { "error" => 'key must not be blank', "bad_key" => key }
            end
            if key.class != String
                return { "error" => 'key must be string type', "bad_key" => key }
            end

            if !/[a-zA-Z0-9_\- ]+$/.match(key)
                return { "error"=>'key must be simple text', "bad_key"=> key }
            end
            
            if ![Fixnum, Float, String, TrueClass, FalseClass, NilClass].include?(value.class)
                value = value.to_s
            end
            jdata[key] = value
        end
        return jdata
    end


    def ScraperWiki.save_sqlite(unique_keys, data, table_name="swdata", verbose=2)
        if !data
            ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => "EMPTY SAVE IGNORED"})
            return
        end

        if data.class == Hash:
            rjdata = convdata(unique_keys, data)
            if rjdata.include?("error")
                raise SqliteException.new(rjdata["error"])
            end
        else
            rjdata = [ ]
            for ldata in data
                ljdata = convdata(unique_keys, ldata)
                if ljdata.include?("error")
                    raise SqliteException.new(ljdata["error"])
                end
                rjdata.push(ljdata)
            end
        end

        ds = SW_DataStore.create()
        res = ds.request(['save_sqlite', unique_keys, rjdata, table_name])
        if res["error"]
            raise SqliteException.new(res["error"])
        end

        if verbose >= 2
            pdata = { }
            if rjdata.class == Hash
                sdata = rjdata
            else
                sdata = rjdata[0]
            end
            sdata.each_pair do |key, value|
                key = ScraperWiki._unicode_truncate(key.to_s, 50)
                if value == nil
                    value  = ''
                else
                    value = ScraperWiki._unicode_truncate(value.to_s, 50)
                end
                pdata[key] = value
            end
            if rjdata.class == Array and rjdata.size > 1
                pdata["number_records"] = "Number Records: "+String(rjdata.size)
            end
            ScraperWiki.dumpMessage({'message_type' => 'data', 'content' => pdata})
        end
        return res
    end

            # also needs to handle the types better (could save json and datetime objects handily
    def ScraperWiki.save_var(name, value, verbose=2)
        data = { "name" => name, "value_blob" => value, "type" => value.class }
        ScraperWiki.save_sqlite(unique_keys=["name"], data=data, table_name="swvariables", verbose=verbose)
    end

    def ScraperWiki.get_var(name, default=nil, verbose=2)
        begin
            result = ScraperWiki.sqlitecommand("execute", "select value_blob, type from swvariables where name=?", [name,], verbose)
        rescue NoSuchTableSqliteException => e   
            return default
        end

        if !result["data"]
            return default
        end
        return result["data"][0][0]
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
