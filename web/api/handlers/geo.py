from api.handlers.api_base import APIBase
from api.external.datastore import Datastore
from piston.utils import rc

class PostcodeToLatLng(APIBase):
    required_arguments = ['postcode', 'country_code']

    def value(self, request):
        # try and get from datastore
        postcode = request.GET.get('postcode', None)
        country_code = request.GET.get('country_code', None)            

        datastore = Datastore()
        result = datastore.postcode_lookup(postcode, country_code)

        if result:
            return result
        
        error_response = rc.BAD_REQUEST
        error_response.write(": No postcode found")
        return error_response

