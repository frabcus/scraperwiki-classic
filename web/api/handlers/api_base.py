from django.core.cache import cache
from web.scraper.models import Scraper
from piston.handler import BaseHandler
from piston.utils import rc
from api.models import api_key
from settings import MAX_API_ITEMS
import sys

class APIBase(BaseHandler):
    allowed_methods = ('GET',)
    result = None
    error_response = False
    cache_duration = 0
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
        if request.GET.get('explorer_user_run', None) == '1':
            request_api_key = 'explorer'
        else:
            request_api_key = api_key.objects.get(
                key=request.GET.get('key', None),
                active=True,
                )
        return True

    def validate(self, request):

        #valid API key?
        if not self.is_valid_api_key(request):
            self.error_response = rc.FORBIDDEN
            self.error_response.write(": Invalid or inactive API key")

        #all required arguments passed?
        for required_argument in self.required_arguments:
            argument_value = request.GET.get(required_argument, None)
            if argument_value == None:
                self.error_response = rc.BAD_REQUEST
                self.error_response.write(": Missing required argument '%s'" % required_argument)

    def read(self, request):

        #reset previous value, piston will persist instances of this class across calls
        self.result = None

        #get the result out of cache if it is there and this call is set to be cached
        if self.cache_duration > 0:
            key = request.path_info + request.META['QUERY_STRING']
            cached_result = cache.get(key)

            if cached_result != None:
                self.error_response = cached_result['error_response']
                self.result = cached_result['result']                

        # validate and set the result (unless we have already retrieved the answer from cache)
        if self.result == None:
            self.validate(request)

        #if this call is set to cache, save the result
        if self.cache_duration > 0:
            result_to_cache = {'error_response': self.error_response, 'result': self.result}
            cache.set(key, result_to_cache, 30)

        #we have an error, return the error response
        if self.error_response != False:
            return None, self.error_response
        else:
            return self.result

    def get_scraper(self, request):
        scraper = None 
        short_name = request.GET.get('name', None)
        try:
            scraper = Scraper.objects.get(short_name=short_name)
        except Exception, e:
            scraper = None

        if scraper != None and scraper.published == False:
            scraper = None

        return scraper

    def clamp_limit(self, limit):
        if limit == 0 or limit > MAX_API_ITEMS:
            limit = MAX_API_ITEMS
        return limit            