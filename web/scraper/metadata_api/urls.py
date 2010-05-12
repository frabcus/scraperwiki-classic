from django.conf.urls.defaults import *
from piston.resource import Resource

from handlers import ScraperMetadataHandler
from auth import ScraperAuth

metadata = Resource(handler=ScraperMetadataHandler, authentication=ScraperAuth())

urlpatterns = patterns('',
    url('^(?P<scraper_guid>[\w_\-]+)/(?P<metadata_name>[\w\s_\-]+)/$', metadata),
)
