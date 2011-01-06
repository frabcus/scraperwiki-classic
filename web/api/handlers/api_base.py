from django.core.cache import cache
from web.codewiki.models import Scraper, Code
from piston.handler import BaseHandler
from piston.utils import rc
from piston.emitters import Emitter
from api.models import api_key
from api.emitters import CSVEmitter, PHPEmitter, GVizEmitter
from settings import MAX_API_ITEMS, DEFAULT_API_ITEMS
import datetime
import sys
import re

Emitter.register('csv', CSVEmitter, 'text/csv; charset=utf-8')
Emitter.register('php', PHPEmitter, 'text/plain; charset=utf-8')
Emitter.register('gviz', GVizEmitter, 'text/plain; charset=utf-8')

class InvalidScraperException(Exception): pass

class APIBase(BaseHandler):
    allowed_methods = ('GET',)
    result = None
    error_response = False
    required_arguments = []

    def has_errors(self):
        return self.error_response != False

    def is_valid_api_key(self, request):
        """
        Looks at the request, checks for a valid API key or explorer_user_run key
        and returns True or False.

        explorer_user_run is for the API explorer only, and should be hidden in 
        some way!
        """
        #result = False
        #if request.GET.get('explorer_user_run', None) == '1':
        #    result = True
        #else:
        #    key = request.GET.get('key', None)
        #    if key and api_key.objects.filter(key=key, active=True).count() == 1:
        #        result = True
        #return result
        return True

    
    
    def validate_argsapikey(self, request):
        #valid API key?
        if not self.is_valid_api_key(request):
            error_response = rc.FORBIDDEN   # these rc.ERROR things return a "fresh" instance of the object
            error_response.write(": Invalid or inactive API key")
            return error_response

        #all required arguments passed?
        for required_argument in self.required_arguments:
            if required_argument not in request.GET:
                error_response = rc.BAD_REQUEST
                error_response.write(": Missing required argument '%s'" % required_argument)
                return error_response
        
        return None
    
    
    def read(self, request):
        error_response = self.validate_argsapikey(request)
        if error_response:
            return error_response
        
        try:
            result = self.value(request)
        except InvalidScraperException:
            error_response = rc.NOT_FOUND
            error_response.write(": Scraper not found")
            return error_response

        return result


    def get_scraper_lsm(self, name):
        try:
            code = Code.unfiltered.get(short_name=name)   # unfiltered is objects, but working around the "convenient" filter that has been injected into the manager
        except:
            return None, { "status":"Does not exist" }
        
        if code.wiki_type == "scraper":
            code = code.scraper
        if code.deleted:
            return code, { "status":"deleted" }
        if not code.published:
            return code, { "status":"unpublished" }
        return code, None
        

    def get_limit_and_offset(self, request):
        try:
            limit = self.clamp_limit(int(request.GET.get('limit')))
        except:
            limit = DEFAULT_API_ITEMS

        try:
            offset = int(request.GET.get('offset'))
        except:
            offset = 0

        return limit, offset

    def clamp_limit(self, limit):
        if limit == 0 or limit > MAX_API_ITEMS:
            limit = MAX_API_ITEMS
        return limit

    def convert_date(self, date_str):
        if not date_str:
            return None
        try:
            #return datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return datetime.datetime(*map(int, re.findall("\d+", date_str)))  # should handle 2011-01-05 21:30:37
        except ValueError:
            return None
    
