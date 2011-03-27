require 'json'
require 'uri'
require 'net/http'
require 'generator'
require 'cgi'

$apiurl = "http://api.scraperwiki.com/api/1.0/datastore/"

$attacheddata = [ ]

module SW_APIWrapper
    def SW_APIWrapper.get_url(url)
        Net::HTTP.get(URI.parse(url))
    end
    
    def SW_APIWrapper.getKeys(name)
        if !$attacheddata.include?(name)
            puts "*** instead of getKeys('"+name+"') please use\n    ScraperWiki.attach('"+name+"') \n    print ScraperWiki.sqliteexecute('select * from `"+name+"`.swdata limit 0')['keys']"
            ScraperWiki.attach(name)
            $attacheddata.push(name)
        end
        result = ScraperWiki.sqliteexecute("select * from `"+name+"`.swdata limit 0")
        if result.include?("error")
            raise SqliteException.new(result["error"])
        end
        return result["keys"]
    end

    def SW_APIWrapper.getData(name, limit=-1, offset=0)
        if !$attacheddata.include?(name)
            puts "*** instead of getData('"+name+"') please use\n    ScraperWiki.attach('"+name+"') \n    print ScraperWiki.select('* from `"+name+"`.swdata')"
            ScraperWiki.attach(name)
            $attacheddata.push(name)
        end

        apilimit = 500
        g = Generator.new do |g|
            count = 0
            while true
                if limit == -1
                    step = apilimit
                else
                    step = apilimit < (limit - count) ? apilimit : limit - count
                end
                query = "* from `#{name}`.swdata limit #{step} offset #{offset+count}"

                records = ScraperWiki.select(query)
                for r in records
                    g.yield r
                end

                count += records.length
                if records.length < step
                    break
                end
                if limit != -1 and count >= limit
                    break
                end
            end
        end
    end

    
    def SW_APIWrapper.getDataByDate(name, start_date, end_date, limit=-1, offset=0)
        raise SqliteException.new("getDataByDate has been deprecated")
    end
    
    def SW_APIWrapper.getDataByLocation(name, lat, lng, limit=-1, offset=0)
        raise SqliteException.new("getDataByLocation has been deprecated")
    end
        
    def SW_APIWrapper.search(name, filtermap, limit=-1, offset=0)
        raise SqliteException.new("SW_APIWrapper.search has been deprecated")
    end
end
