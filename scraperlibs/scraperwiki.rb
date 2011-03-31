require 'json'
require	'uri'
require	'net/http'
require 'scraperwiki/datastore'
require 'scraperwiki/metadata'
require 'scraperwiki/apiwrapper'

class SqliteException < RuntimeError
end

class NoSuchTableSqliteException < SqliteException
end

module ScraperWiki

    $cacheFor = 0
    $metacallholder = nil

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

    def ScraperWiki._follow_redirects(response, limit = 10)
      # You should choose better exception.
      raise ArgumentError, 'HTTP redirect too deep' if limit == 0

      #response = Net::HTTP.get_response(uri)
      case response
        when Net::HTTPSuccess then 
          response
        when Net::HTTPRedirection then 
          new_response = Net::HTTP.get_response(URI.parse(response['location']))
          _follow_redirects(new_response, limit - 1)
        else
          response.error!
      end
    end

    def ScraperWiki.scrape(url, params = nil)
        uri  = URI.parse(url)
        if params.nil?
            response = Net::HTTP.get_response(uri)
        else
            if uri.path == ''
                uri.path = '/' # must post to a path
            end
            response = Net::HTTP.post_form(uri, params)
        end
        
        return ScraperWiki._follow_redirects(response).body
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


    def ScraperWiki._unicode_truncate(string, size)
        # Stops 2 byte unicode characters from being chopped in half which kills JSON serializer
        string.scan(/./u)[0,size].join
    end

    def ScraperWiki.save(unique_keys, data, date=nil, latlng=nil, table_name="swdata")
        if unique_keys != nil && !unique_keys.kind_of?(Array)
            raise 'unique_keys must be nil or an array'
        end

        ds = SW_DataStore.create()

        ldata = data.dup
        if date != nil
            ldata["date"] = date
        end
        if latlng != nil
            ldata["latlng_lat"] = latlng[0]
            ldata["latlng_lng"] = latlng[1]
        end
        return ScraperWiki.save_sqlite(unique_keys, ldata, table_name="swdata", verbose=2)
    end


        # this ought to be a local function (the other sqlite functions go through it)
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
            result = ScraperWiki.sqliteexecute("select value_blob, type from swvariables where name=?", name, verbose)
        rescue NoSuchTableSqliteException => e   
            return default
        end
        if result["data"].length == 0
            return default
        end
        return result["data"][0][0]
    end

    def ScraperWiki.get_metadata(metadata_name, default = nil)
        if $metacallholder == nil
            puts "*** instead of get_metadata('"+metadata_name+"') please use\n    get_var('"+metadata_name+"')"
            $metacallholder = "9sd8sd9fs9d8f9s8df9s8f"
        end
        result = ScraperWiki.get_var(metadata_name, $metacallholder)
        if result == $metacallholder
            result = SW_MetadataClient.create().get(metadata_name, default) 
        end
        return result
    end

    def ScraperWiki.save_metadata(metadata_name, value)
        #return SW_MetadataClient.create().save(metadata_name, value)
        if $metacallholder == nil
            puts "*** instead of metadata.save('"+metadata_name+"') please use\n    scraperwiki.sqlite.save_var('"+metadata_name+"')"
            $metacallholder = "9sd8sd9fs9d8f9s8df9s8f"
        end
        return ScraperWiki.save_var(metadata_name, value)
    end


    def ScraperWiki.show_tables(dbname=nil)
        name = "sqlite_master"
        if dbname != nil
            name = "`"+dbname+"`.sqlite_master" 
        end
        result = ScraperWiki.sqlitecommand("execute", val1="select tbl_name, sql from "+name+" where type='table'")
        #return result["data"]
        return (Hash[*result["data"].flatten])   # pre-1.8.7
    end


    def ScraperWiki.table_info(name)
        sname = name.split(".")
        if sname.length == 2
            result = sqlitecommand("execute", "PRAGMA %s.table_info(`%s`)" % sname)
        else
            result = sqlitecommand("execute", "PRAGMA table_info(`%s`)" % name)
        end
        res = [ ]
        for d in result["data"]
            res.push(Hash[*result["keys"].zip(d).flatten])   # pre-1.8.7
        end
        return res
    end


    def ScraperWiki.getKeys(name)
        return SW_APIWrapper.getKeys(name)
    end

    def ScraperWiki.getData(name, limit=-1, offset=0)
        SW_APIWrapper.getData(name, limit, offset)
    end
    
    def ScraperWiki.getDataByDate(name, start_date, end_date, limit=-1, offset=0)
        raise SqliteException.new("getDataByDate has been deprecated")
    end
    
    def ScraperWiki.getDataByLocation(name, lat, lng, limit=-1, offset=0)
        SW_APIWrapper.getDataByLocation(name, lat, lng, limit, offset)
    end
        
    def ScraperWiki.search(name, filterdict, limit=-1, offset=0)
        SW_APIWrapper.search(name, filterdict, limit, offset)
    end


    def ScraperWiki.attach(name, asname=nil, verbose=1)
        return ScraperWiki.sqlitecommand("attach", name, asname, verbose)
    end
    
    def ScraperWiki.sqliteexecute(val1, val2=nil, verbose=1)
        if val2 != nil && val1.scan(/\?/).length != 0 && val2.class != Array
            val2 = [val2]
        end
        return ScraperWiki.sqlitecommand("execute", val1, val2, verbose)
    end

    def ScraperWiki.commit(verbose=1)
        return ScraperWiki.sqlitecommand("commit", nil, nil, verbose)
    end

    def ScraperWiki.select(val1, val2=nil, verbose=1)
        if val2 != nil && val1.scan(/\?/).length != 0 && val2.class != Array
            val2 = [val2]
        end
        result = ScraperWiki.sqlitecommand("execute", "select "+val1, val2, verbose)
        res = [ ]
        for d in result["data"]
            #res.push(Hash[result["keys"].zip(d)])           # post-1.8.7
            res.push(Hash[*result["keys"].zip(d).flatten])   # pre-1.8.7
        end
        return res
    end

end
