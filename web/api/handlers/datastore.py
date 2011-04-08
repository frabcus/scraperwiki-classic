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


def data_dictlist(scraper_id, short_name, tablename="", limit=1000, offset=0, start_date=None, end_date=None, latlng=None):
    dataproxy = DataStore(scraper_id, short_name)  
    rc, arg = dataproxy.data_dictlist(tablename, limit, offset, start_date, end_date, latlng)
    if rc:
        return arg
    
    # quick helper result for api when it searches on the default table (which is selected deep in the dataproxy after it has checked out the original mysql key-value datastore thing)
    if arg == "sqlite3.Error: no such table: main.swdata":
        sqlitedata = dataproxy.request(("sqlitecommand", "datasummary", 0, None))
        if sqlitedata and type(sqlitedata) not in [str, unicode]:
            return [{"error":arg}, {'datasummary':sqlitedata}]
    raise Exception(arg)


# accessible only through api/datastore/getolddata
class Data(APIBase):
    required_arguments = ['name']
    def value(self, request):
        scraper = self.getscraperorrccode(request, request.GET.get('name'), "apidataread")
        limit, offset, tablename = requestvalues(request)
        return data_dictlist(scraper_id=scraper.guid, short_name=scraper.short_name, tablename=tablename, limit=limit, offset=offset)


class Keys(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with format=jsonlist and limit 0" }

class Search(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"no search is possible across different databases" }

class DataByLocation(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite bounds on the lat lng values" }

class DataByDate(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with bounds on your date field" }

