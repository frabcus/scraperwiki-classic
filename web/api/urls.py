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
    url(r'^1\.0/scraperwiki.scraper.search/$', 'django.views.generic.simple.direct_to_template', {'template': 'scraper_search_1.0.html'}, name='scraper_search'),
    url(r'^1\.0/scraperwiki.scraper.search/explore/$', views.explore_scraper_search, name='explore_scraper_search'),

    
    # API calls
    url(r'^1\.0/scraper/getinfo/(?P<short_name>[\-\w]+)$', scraperinfo_handler),
    url(r'^1\.0/scraper/getdata/(?P<short_name>[\-\w]+)$', data_handler),
)