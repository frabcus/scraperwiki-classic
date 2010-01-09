from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.conf import settings

from tagging.models import Tag

from piston.handler import BaseHandler
from piston.utils import rc
import emitters
from scraper.models import Scraper

from models import api_key


def valid_api_key(request):
    """
    Looks at the request, checks for a valid API key or explorer_user_run key
    and returns True or False.
    
    
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
    
   
def invlaid_api_key():
    resp = rc.FORBIDDEN
    resp.write(": Invalid or inactive API key")
    return resp
    
 
class ScraperInfoHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, short_name):
        
        if not valid_api_key(request):
            return invlaid_api_key()
        
        try:
            scraper = Scraper.objects.get(short_name=short_name)
        except Exception, e:
            resp = rc.BAD_REQUEST
            resp.write(": No scraper named '%s'" % short_name)
            return resp
            
        info = {}
        info['license'] = scraper.license
        info['created'] = scraper.created_at
        info['last_run'] = scraper.last_run
        info['records'] = scraper.record_count()
        info['short_name'] = scraper.short_name
        info['language'] = scraper.language()
        info['tags'] = [tag.name for tag in Tag.objects.get_for_object(scraper)]
        return [info,]

class GetDataHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, short_name):
        
        if not valid_api_key(request):
            return invlaid_api_key()
            
        try:
            scraper = Scraper.objects.get(short_name=short_name)
        except Exception, e:
            resp = rc.BAD_REQUEST
            resp.write(": No scraper named '%s'" % short_name)
            return resp
        
        limit = request.GET.get('limit', 100)
        offset = request.GET.get('offset', 0)

        #check if the limit is > than the max allowed, if it is then reset it
        if limit > MAX_API_ITEMS:
            limit = MAX_API_ITEMS
        
        data = Scraper.objects.data_summary(scraper_id=scraper.guid, limit=limit, offset=offset)
        
        # We need to change the data format slightly
        # Now each item is a dict, in a list
        items = []
        for row in data['rows']:
            item = {}
            for k,v in enumerate(row):
                item[data['headings'][k]] = v
            items.append(item)
        return items
        
        
        
        
        
        