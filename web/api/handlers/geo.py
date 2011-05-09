from api.handlers.api_base import APIBase
from api.external.datastore import Datastore
from piston.utils import rc

class PostcodeToLatLng(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use the scraperwiki view to do it" }

