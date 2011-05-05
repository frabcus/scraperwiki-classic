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

