require 'json'
require 'uri'
require 'net/http'
require 'generator'
require 'cgi'

$apiurl = "http://api.scraperwiki.com/api/1.0/datastore/"

module SW_APIWrapper
    def SW_APIWrapper.get_url(url)
        Net::HTTP.get(URI.parse(url))
    end
    
    def SW_APIWrapper.getKeys(name)
        url = "%sgetkeys?&name=%s" % [$apiurl, name]
        ljson = get_url(url)
        return JSON.parse(ljson)
    end

    def SW_APIWrapper.generateData(urlbase, limit, offset)
        apilimit = 500
        g = Generator.new do |g|
            count = 0
            while true
                if limit == -1
                    step = apilimit
                else
                    step = apilimit < (limit - count) ? apilimit : limit - count
                end

                url = "#{urlbase}&limit=#{step}&offset=#{offset+count}"
                records = JSON.parse(ScraperWiki.scrape(url))
                for r in records
                    g.yield r
                end

                count += records.length

                if records.length < step
                    # run out of records
                    break
                end

                if limit != -1 and count >= limit
                    # exceeded the limit
                    break
                end
            end
        end
    end

    def SW_APIWrapper.getData(name, limit=-1, offset=0)
        urlbase = "#{$apiurl}getdata?name=#{name}"
        SW_APIWrapper.generateData(urlbase, limit, offset)
    end
    
    def SW_APIWrapper.getDataByDate(name, start_date, end_date, limit=-1, offset=0)
        urlbase = "#{$apiurl}getdatabydate?name=#{name}&start_date=#{start_date}&end_date=#{end_date}"
        SW_APIWrapper.generateData(urlbase, limit, offset)
    end
    
    def SW_APIWrapper.getDataByLocation(name, lat, lng, limit=-1, offset=0)
        urlbase = "#{$apiurl}getdatabydate?name=#{name}&lat=#{lat}&lng=#{lng}"
        SW_APIWrapper.generateData(urlbase, limit, offset)
    end
        
    def SW_APIWrapper.search(name, filtermap, limit=-1, offset=0)
        res = []
        filtermap.each do |k, v|
            key = CGI.escape k
            value = CGI.escape v
            res.push "%s,%s" % [key, value]
        end
        filter = res.join("|")
        urlbase = "#{$apiurl}search?name=#{name}&filter=#{filter}"
        return SW_APIWrapper.generateData(urlbase, limit, offset)
    end
end
