from django.core.cache import cache
from web.codewiki.models import Scraper, Code
from piston.handler import BaseHandler
from piston.utils import rc
from piston.emitters import Emitter
from api.models import api_key
from api.emitters import CSVEmitter, PHPEmitter, GVizEmitter, JSONDICTEmitter
import datetime
import sys
import re

Emitter.register('jsondict', JSONDICTEmitter, 'application/json; charset=utf-8')
Emitter.register('csv', CSVEmitter, 'text/csv; charset=utf-8')
Emitter.register('php', PHPEmitter, 'text/plain; charset=utf-8')
Emitter.register('gviz', GVizEmitter, 'text/plain; charset=utf-8')


class ScraperAPINotFound(Exception): pass
class ScraperAPIForbidden(Exception): pass
class ScraperAPIError(Exception): pass

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
            # this is the function everything funnels through
            result = self.value(request)
            
                    # piston appears not to handle these responses properly.  for now return json objects with messages in them
        except ScraperAPINotFound, e:
            return { "error":"Sorry, this scraper is not found." }
            error_response = rc.NOT_FOUND
            error_response.write(": Scraper not found")
            return error_response
        except ScraperAPIForbidden, e:
            return { "error":"Sorry, this scraper appears to be private." }
            error_response = rc.FORBIDDEN
            error_response.write(": You do not have access to this scraper")
            return error_response
        except ScraperAPIError, e:
            return { "error":"Sorry, there is an error in your request." }
            error_response = rc.BAD_REQUEST
            error_response.write(": Error "+e.message)
            return error_response
        return result


    def getscraperorrccode(self, request, short_name, action):
        try:
            scraper = Code.unfiltered.get(short_name=short_name)
        except Code.DoesNotExist:
            raise ScraperAPINotFound()
        if not scraper.actionauthorized(request.user, action):
            raise ScraperAPIForbidden()
        return scraper


    def convert_date(self, date_str):
        if not date_str:
            return None
        try:
            #return datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return datetime.datetime(*map(int, re.findall("\d+", date_str)))  # should handle 2011-01-05 21:30:37
        except ValueError:
            return None
    
