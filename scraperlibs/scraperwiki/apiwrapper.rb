# code to be ported to scraperlibs once complete

require 'json'
require 'uri'
require 'net/http'

$apiurl = "http://api.scraperwiki.com/api/1.0/datastore/"
$apilimit = 500


module SW_APIWrapper
    def SW_APIWrapper.get_url(url)
        puts url
        Net::HTTP.get(URI.parse(url))
    end
    
    def SW_APIWrapper.getKeys(name)
        url = "%sgetkeys?&name=%s" % [$apiurl, name]
        ljson = get_url(url)
        return JSON.parse(ljson)
    end

    def SW_APIWrapper.generateData(urlbase, limit, offset)
        count = 0
        loffset = 0
        while true
            if limit == -1
                llimit = $apilimit
            else
                llimit = [$apilimit, limit-count].min
            end
    
            url = "%s&limit=%s&offset=%d" % [urlbase, llimit, offset+loffset]
            ljson = get_url(url)
            lresult = JSON.parse(ljson)
            lenresult = 0
            for row in lresult
                yield row
                lenresult += 1
            end

            count += lenresult
            if lenresult < llimit  # run out of records
                break
            end
                
            if limit != -1 and count >= limit    # exceeded the limit
                break
            end
    
            loffset += llimit
        end
    end

    def SW_APIWrapper.getData(name, limit=-1, offset=0)
        urlbase = "%sgetdata?name=%s" % [$apiurl, name]
        SW_APIWrapper.generateData(urlbase, limit, offset) {|i| yield i}
    end
    
    def SW_APIWrapper.getDataByDate(name, start_date, end_date, limit=-1, offset=0)
        urlbase = "%sgetdatabydate?name=%s&start_date=%s&end_date=%s" % [$apiurl, name, start_date, end_date]
        SW_APIWrapper.generateData(urlbase, limit, offset) {|i| yield i}
    end
    
    def SW_APIWrapper.getDataByLocation(name, lat, lng, limit=-1, offset=0)
        urlbase = "%sgetdatabylocation?name=%s&lat=%f&lng=%f" % [$apiurl, name, lat, lng]
        SW_APIWrapper.generateData(urlbase, limit, offset) {|i| yield i}
    end
        
    def SW_APIWrapper.search(name, filterdict, limit=-1, offset=0)
        raise "unfinished"
        #filter = map(lambda x: "%s,%s" % [urllib.quote(x[0]), urllib.quote(x[1])], filterdict.items()).join("|")
        urlbase = "%ssearch?name=%s&filter=%s" % [$apiurl, name, filter]
        SW_APIWrapper.generateData(urlbase, limit, offset) {|i| yield i}
    end
end