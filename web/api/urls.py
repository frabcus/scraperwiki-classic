from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from piston.resource import Resource
from handlers import ScraperInfoHandler, GetDataHandler

from api import views

scraperinfo_handler = Resource(ScraperInfoHandler)
data_handler = Resource(GetDataHandler)

# Version 1.0 URLS
urlpatterns = patterns('',

    # Standard Views
    url(r'^keys$', views.keys, name='keys'),
    
    # Documentation
    url(r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'index.html'}),
    url(r'^1\.0/$', 'django.views.generic.simple.direct_to_template', {'template': '1.0.html'}, name='index'),
    
    # API calls
    url(r'^1\.0/scraper/getinfo/(?P<short_name>[\-\w]+)$', scraperinfo_handler),
    url(r'^1\.0/scraper/getdata/(?P<short_name>[\-\w]+)$', data_handler),
)