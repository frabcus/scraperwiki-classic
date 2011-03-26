from api.handlers.api_base import APIBase
from web.codewiki.models import Scraper
import datetime
from piston.utils import rc
from settings import MAX_API_ITEMS, DEFAULT_API_ITEMS
from codewiki.managers.datastore import DataStore

    

def requestvalues(request):
    try:
        limit = int(request.GET.get('limit', ""))
    except ValueError:
        limit = DEFAULT_API_ITEMS
    
    if limit < 1:
        limit = DEFAULT_API_ITEMS
    if limit > MAX_API_ITEMS:
        limit = MAX_API_ITEMS
        
    try:
        offset = int(request.GET.get('offset', ""))
    except ValueError:
        offset = 0
    
    if offset < 0:
        offset = 0

    tablename = request.GET.get('tablename', "")
    
    return limit, offset, tablename




# keys for a table (to be deprecated) -- get table with limit 1 instead
class Keys(APIBase):
    required_arguments = ['name']

    def value(self, request):
        return { "error":"Sorry, this function has been deprecated." }
        scraper = self.getscraperorrccode(request, request.GET.get('name'), "apiread")
        dataproxy = DataStore(scraper.guid, "")
        rc, arg = dataproxy.request(('datastore_keys',))
        if not rc :
            raise ScraperAPIError(arg)
        return arg



class Search(APIBase):
    required_arguments = ['name', 'filter']

    def value(self, request):
        return { "error":"Sorry, this function has been deprecated." }
        scraper = self.getscraperorrccode(request, request.GET.get('name'), "apiread")
        
        key_values = []
        kv_string = request.GET.get('filter', None)
        kv_split = kv_string.split('|') 
        for item in kv_split:
            item_split = item.split(',', 1)
            if len(item_split) == 2:
                key_values.append((item_split[0], item_split[1]))
        if len(key_values) == 0:
            raise ScraperAPIError("No keys set")
        
        limit, offset, tablename = requestvalues(request)
        dataproxy = DataStore(scraper.guid, "")
        dataproxy.request(('data_search', key_values, limit, offset))
        if not rc :
            raise ScraperAPIError(arg)
        return arg
        


class Data(APIBase):
    required_arguments = ['name']
    
    def value(self, request):
        scraper, lsm = self.get_scraper_lsm(request.GET.get('name'))
        if lsm:
            return [lsm]
        
        limit, offset, tablename = requestvalues(request)
        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, short_name=scraper.short_name, tablename=tablename, limit=limit, offset=offset)


class DataByLocation(APIBase):
    required_arguments = ['name', 'lat', 'lng']

    def value(self, request):
        return { "error":"Sorry, this function has been deprecated." }
        scraper, lsm = self.get_scraper_lsm(request.GET.get('name'))
        if lsm:
            return [lsm]
        
        limit, offset, tablename = requestvalues(request)
        try:
            latlng = (float(request.GET.get('lat', None)), float(request.GET.get('lng', None)))
        except:
            error_response = rc.BAD_REQUEST
            error_response.write(": Invalid lat/lng format")
            return error_response

        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, short_name=scraper.short_name, tablename="", limit=limit, offset=offset, latlng=latlng)


class DataByDate(APIBase):
    required_arguments = ['name', 'start_date', 'end_date']

    def value(self, request):
        return { "error":"Sorry, this function has been deprecated." }
        scraper, lsm = self.get_scraper_lsm(request.GET.get('name'))
        if lsm:
            return [lsm]
        
        limit, offset, tablename = requestvalues(request)
        start_date = self.convert_date(request.GET.get('start_date', None))
        end_date = self.convert_date(request.GET.get('end_date', None))

        if not start_date and not end_date:
            error_response = rc.BAD_REQUEST
            error_response.write(": Invalid date format")
            return error_response
                
        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, short_name=scraper.short_name, tablename="", limit=limit, offset=offset, start_date=start_date, end_date=end_date)

