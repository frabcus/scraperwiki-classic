from api.handlers.api_base import APIBase
from api.external.datastore import Datastore

class PostcodeToLatLng(APIBase):
    required_arguments = ['postcode', 'country_code']
    cache_duration = 10
        
    def validate(self, request):
        super(PostcodeToLatLng, self).validate(request)

        if self.has_errors() == False:
            # try and get from datastore
            postcode = request.GET.get('postcode', None)
            country_code = request.GET.get('country_code', None)            

            datastore = Datastore()
            result = datastore.postcode_lookup(postcode, country_code)

            if result == None:
                self.error_response = rc.BAD_REQUEST
                self.error_response.write(": No postcode found")
            else:
                #all is well
                self.result = result