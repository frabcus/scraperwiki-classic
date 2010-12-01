from django.conf.urls.defaults import *
from piston.resource import Resource

from handlers import ScraperMetadataHandler

metadata = Resource(handler=ScraperMetadataHandler)

urlpatterns = patterns('',
    url('^(?P<scraper_guid>[\w_\-]+)/(?P<metadata_name>.+)/$', metadata, name='metadata_api'),
)
