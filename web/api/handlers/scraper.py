from web.scraper.models import Scraper
from api.handlers.api_base import APIBase
from tagging.models import Tag
from piston.utils import rc

class GetInfo(APIBase):

    def validate(self, request):
        super(GetInfo, self).validate(request)
        
        if self.has_errors() == False:
            scraper = self.get_scraper(request)
            if scraper != None and self.has_errors() == False:
                info = {}
                info['license']     = scraper.license
                info['created']     = scraper.created_at
                info['last_run']    = scraper.last_run
                info['records']     = scraper.record_count
                info['short_name']  = scraper.short_name
                info['language']    = scraper.language()
                info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
                self.result = [info,]
            else:
                self.error_response = rc.BAD_REQUEST
                self.error_response.write(": No found scraper by that name")


class Search(APIBase):
    required_arguments = ['query']
    
    def validate(self, request):
        super(Search, self).validate(request)

        if self.has_errors() == False:
            self.result = Scraper.objects.search(q)