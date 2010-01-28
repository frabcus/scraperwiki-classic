from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from piston.resource import Resource
from handlers import ScraperInfoHandler, GetDataHandler, ScraperSearchHandler, GetDataByDateHandler, GetDataByLocationHandler

from api import views

scraperinfo_handler = Resource(ScraperInfoHandler)
data_handler = Resource(GetDataHandler)
scrapersearch_handler = Resource(ScraperSearchHandler)
getdatabydate_handler = Resource(GetDataByDateHandler)
getdatabylocation_handler = Resource(GetDataByLocationHandler)


# Version 1.0 URLS
urlpatterns = patterns('',

    # Standard Views
    url(r'^keys$', views.keys, name='keys'),

    # Documentation
    url(r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'index.html'}),
    url(r'^1\.0/$', 'django.views.generic.simple.direct_to_template', {'template': '1.0.html'}, name='index'),
    url(r'^1\.0/libraries/$', 'django.views.generic.simple.direct_to_template', {'template': 'libraries.html'}, name='libraries'),
    url(r'^1\.0/explore/scraperwiki.scraper.search/$', views.explore_scraper_search_1_0, name='scraper_search'),
    url(r'^1\.0/explore/scraperwiki.scraper.getinfo/$', views.explore_scraper_getinfo_1_0, name='scraper_getinfo'),    
    url(r'^1\.0/explore/scraperwiki.scraper.getdata/$', views.explore_scraper_getdata_1_0, name='scraper_getdata'),    
    url(r'^1\.0/explore/scraperwiki.scraper.getdatabydate/$', views.explore_scraper_getdatabydate_1_0, name='scraper_getdatabydate'),
    url(r'^1\.0/explore/scraperwiki.scraper.getdatabylocation/$', views.explore_scraper_getdatabylocation_1_0, name='scraper_getdatabylocation'),    

    # API calls

    #explorer
    url(r'^explorer_call$', views.explorer_user_run, name='explorer_call'),
    url(r'^explorer_example/(?P<method>[\w_\-\.\_]+)/$', views.explorer_example, name='explorer_example'),    

    url(r'^1\.0/scraper/search/$', scrapersearch_handler, name="method_search"),
    url(r'^1\.0/scraper/getinfo/$', scraperinfo_handler, name="method_getinfo"),
    url(r'^1\.0/scraper/getdata/$', data_handler, name="method_getdata"),
    url(r'^1\.0/scraper/getdatabydate/$', getdatabydate_handler, name="method_getdatabydate"),    
    url(r'^1\.0/scraper/getdatabylocation/$', getdatabylocation_handler, name="method_getdatabylocation"),        

)
