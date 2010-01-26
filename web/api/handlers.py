from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.conf import settings

from tagging.models import Tag

from piston.handler import BaseHandler
from piston.utils import rc
import emitters
from scraper.models import Scraper

from settings import MAX_API_ITEMS

from models import api_key
import re
import datetime


def is_valid_api_key(request):
    """
    Looks at the request, checks for a valid API key or explorer_user_run key
    and returns True or False.
    
    explorer_user_run is for the API exploer only, and should be hidden in 
    some way!
    
    """
    try:
        if request.GET.get('explorer_user_run', None) == '1':
            request_api_key = 'explorer'
        else:
            request_api_key = api_key.objects.get(
                key=request.GET.get('key', None),
                active=True,
                )
        return True
    except:
        return False
    


def get_scraper_response(request):
    '''gets the scraper from the request or produces an error response'''
    allowed_methods = ('GET',)
    
    if not is_valid_api_key(request):
        error_response = rc.FORBIDDEN
        error_response.write(": Invalid or inactive API key")
        return None, error_response

    short_name = request.GET.get('name', None)
    try:
        scraper = Scraper.objects.get(short_name=short_name)
    except Exception, e:
        error_response = rc.BAD_REQUEST
        error_response.write(": No scraper named '%s'" % short_name)
        return None, error_response

    if not scraper.published:
        error_response = rc.BAD_REQUEST
        error_response.write(": Unpublished scraper named '%s'" % short_name)
        return None, error_response
        
    return scraper, None


def clamp_limit(limit):
    if limit == 0 or limit > MAX_API_ITEMS:
        limit = MAX_API_ITEMS
    return limit

class ScraperInfoHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        scraper, error_response = get_scraper_response(request)
        if error_response:
            return error_response
            
        info = {}
        info['license']     = scraper.license
        info['created']     = scraper.created_at
        info['last_run']    = scraper.last_run
        info['records']     = scraper.record_count()
        info['short_name']  = scraper.short_name
        info['language']    = scraper.language()
        info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
        return [info,]



class GetDataHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        limit = clamp_limit(int(request.GET.get('limit', 100)))
        offset = int(request.GET.get('offset', 0))        
        scraper, error_response = get_scraper_response(request)
        if error_response:
            return error_response
        
        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset)
        

def ConvertDate(dateform):
    if not dateform:
        return None
    mdateform = re.match("(\d\d\d\d)-(\d\d)-(\d\d)", dateform)
    if not mdateform:
        return None
    return datetime.datetime(int(mdateform.group(1)), int(mdateform.group(2)), int(mdateform.group(3)))
    
    
class GetDataByDateHandler(BaseHandler):        
    allowed_methods = ('GET',)
        
    def read(self, request):
        limit = clamp_limit(int(request.GET.get('limit', 100)))
        offset = int(request.GET.get('offset', 0))
        scraper, error_response = get_scraper_response(request)
        if error_response:
            return error_response
        
        start_date = ConvertDate(request.GET.get('start_date', None))
        end_date = ConvertDate(request.GET.get('end_date', None))
        
        # raise an error if there's no date range in this request
        if not start_date and not end_date:
            error_response = rc.BAD_REQUEST
            error_response.write(": No date range selected '%s'" % short_name)
            return error_response
        
        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset, start_date=start_date, end_date=end_date)
        


class GetDataByLocationHandler(BaseHandler):                
    allowed_methods = ('GET',)        
        
    def read(self, request):
        
        limit = clamp_limit(int(request.GET.get('limit', 100)))
        offset = int(request.GET.get('offset', 0))
        scraper, error_response = get_scraper_response(request)
        if error_response:
            return error_response
        
        latlng = (float(request.GET.get('lat', None)), float(request.GET.get('lng', None)))

        # raise an error if there's no location in this request
        if not latlng:
            error_response = rc.BAD_REQUEST
            error_response.write(": No latitude or longitude specified '%s'" % short_name)
            return error_response
        
        return Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset, latlng=latlng)
        
        
class ScraperSearchHandler(BaseHandler):        
    allowed_methods = ('GET',)

