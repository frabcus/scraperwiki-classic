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



class Keys(APIBase):
    required_arguments = ['name']

    def value(self, request):
        scraper, lsm = self.get_scraper_lsm(request.GET.get('name'))
        if lsm:
            return [lsm]
        
        if not scraper.published:
            return [{"status":"unpublished"}]
        return Scraper.objects.datastore_keys(scraper_id=scraper.guid)

class Search(APIBase):
    required_arguments = ['name', 'filter']

    def value(self, request):
        scraper, lsm = self.get_scraper_lsm(request.GET.get('name'))
        if lsm:
            return [lsm]
        
        key_values = []
        kv_string = request.GET.get('filter', None)
        kv_split = kv_string.split('|') 
        for item in kv_split:
            item_split = item.split(',', 1)
            if len(item_split) == 2:
                key_values.append((item_split[0], item_split[1]))

        if len(key_values) == 0:
            return rc.BAD_REQUEST
        
        limit, offset, tablename = requestvalues(request)
        
        return Scraper.objects.data_search(scraper_id=scraper.guid, key_values=key_values, limit=limit, offset=offset)
    

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


class Sqlite(APIBase):
    required_arguments = ['name', 'query']
    
    def value(self, request):
        attachlist = request.GET.get('attach', '').split(";")
        attachlist.insert(0, request.GET.get('name'))   # just the first entry on the list
        
        dataproxy = DataStore("sqlviewquery", "")  # zero length short name means it will open up a :memory: database
        for aattach in attachlist:
            if aattach:
                aa = aattach.split(",")
                sqlitedata = dataproxy.request(("sqlitecommand", "attach", aa[0], (len(aa) == 2 and aa[1] or None)))
        
        sqlquery = request.GET.get('query')
        if not sqlquery:
            return HttpResponse("Example:  ?attach=scraper_name,src&query=select+*+from+src.swdata+limit+10")
        
        return dataproxy.request(("sqlitecommand", "execute", sqlquery, None))
