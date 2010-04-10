from api.handlers.api_base import APIBase
from web.scraper.models import Scraper
import re

class Keys(APIBase):
    required_arguments = ['name']

    def validate(self, request):
        super(Keys, self).validate(request)

        if self.has_errors() == False:        
            scraper = self.get_scraper(request)
            self.result = Scraper.objects.datastore_keys(scraper_id=scraper.guid)

class Search(APIBase):
    required_arguments = ['name']
    required_arguments = ['filter']

    def validate(self, request):
        super(Search, self).validate(request)

        if self.has_errors() == False:        

            key_values = []
            kv_string = request.GET.get('filter', None)
            kv_split = kv_string.split('|') 
            for item in kv_split:
                item_split = item.split(',')
                key_values.append((item_split[0], item_split[1]))
            
            limit = self.clamp_limit(int(request.GET.get('limit', 100)))
            offset = int(request.GET.get('offset', 0))
            scraper = self.get_scraper(request)
            self.result = Scraper.objects.data_search(scraper_id=scraper.guid, key_values=key_values, limit=limit, offset=offset)
    

class Data(APIBase):
    required_arguments = ['name']
    
    def validate(self, request):
        super(Data, self).validate(request)

        if self.has_errors() == False:        
            limit = self.clamp_limit(int(request.GET.get('limit', 100)))
            offset = int(request.GET.get('offset', 0))
            scraper = self.get_scraper(request)
            self.result = Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset)


class DataByLocation(APIBase):
    required_arguments = ['name', 'lat', 'lng']

    def validate(self, request):
        super(DataByLocation, self).validate(request)

        if self.has_errors() == False:        

            limit = self.clamp_limit(int(request.GET.get('limit', 100)))
            offset = int(request.GET.get('offset', 0))
            latlng = (float(request.GET.get('lat', None)), float(request.GET.get('lng', None)))            
            scraper = self.get_scraper(request)

            self.result = Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset, latlng=latlng)

class DataByDate(APIBase):
    required_arguments = ['name', 'start_date', 'end_date']

    def validate(self, request):
        super(DataByDate, self).validate(request)

        if self.has_errors() == False:        

            limit = self.clamp_limit(int(request.GET.get('limit', 100)))
            offset = int(request.GET.get('offset', 0))
            start_date = self.convert_date(request.GET.get('start_date', None))
            end_date = self.convert_date(request.GET.get('end_date', None))

            if not start_date and not end_date:
                self.error_response = rc.BAD_REQUEST
                self.error_response.write(": Invalid date format")                
                
            if self.has_errors() == False:        
                scraper = self.get_scraper(request)                
                self.result = Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset, latlng=latlng)

    def convert_date(self, dateform):
        if not dateform:
            return None
        mdateform = re.match("(\d\d\d\d)-(\d\d)-(\d\d)", dateform)
        if not mdateform:
            return None
            
        return datetime.datetime(int(mdateform.group(1)), int(mdateform.group(2)), int(mdateform.group(3)))
