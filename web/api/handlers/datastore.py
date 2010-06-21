from api.handlers.api_base import APIBase
from web.scraper.models import Scraper
import datetime
from piston.utils import rc

class Keys(APIBase):
    required_arguments = ['name']

    def validate(self, request):
        super(Keys, self).validate(request)

        if self.has_errors() == False:        
            scraper = self.get_scraper(request)
            self.result = Scraper.objects.datastore_keys(scraper_id=scraper.guid)

class Search(APIBase):
    required_arguments = ['name', 'filter']

    def validate(self, request):
        super(Search, self).validate(request)

        if self.has_errors() == False:        

            key_values = []
            kv_string = request.GET.get('filter', None)
            kv_split = kv_string.split('|') 
            for item in kv_split:
                item_split = item.split(',', 1)
                if len(item_split) == 2:
                    key_values.append((item_split[0], item_split[1]))

            if len(key_values) == 0:
                self.error_response = rc.BAD_REQUEST
                return
            
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
                self.result = Scraper.objects.data_dictlist(scraper_id=scraper.guid, limit=limit, offset=offset, start_date=start_date, end_date=end_date)

    def convert_date(self, date_str):
        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
