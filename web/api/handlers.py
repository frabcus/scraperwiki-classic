from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound

from tagging.models import Tag

from piston.handler import BaseHandler
from piston.utils import rc
import emitters
from scraper.models import Scraper

from models import api_key

class ScraperInfoHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, short_name):
        
        try:
            request_api_key = api_key.objects.get(
                key=request.GET.get('key', None),
                active=True,
                )
        except:
            resp = rc.FORBIDDEN
            resp.write(": Invalid or inactive API key")
            return resp
                
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
        
        try:
            request_api_key = api_key.objects.get(
                key=request.GET.get('key', None),
                active=True,
                )
        except:
            resp = rc.FORBIDDEN
            resp.write(": Invalid or inactive API key")
            return resp
            
        try:
            scraper = Scraper.objects.get(short_name=short_name)
        except Exception, e:
            resp = rc.BAD_REQUEST
            resp.write(": No scraper named '%s'" % short_name)
            return resp
        
        limit = request.GET.get('limit', 1000)
        offset = request.GET.get('offset', 0)
        
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
        
        
        
        
        
        