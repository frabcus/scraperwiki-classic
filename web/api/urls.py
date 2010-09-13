from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from piston.resource import Resource
from handlers import geo
from handlers import scraper
from handlers import datastore

from api import views

scraperinfo_handler = Resource(scraper.GetInfo)
scrapersearch_handler = Resource(scraper.Search)

data_handler = Resource(datastore.Data)
keys_handler = Resource(datastore.Keys)
datastore_search_handler = Resource(datastore.Search)
getdatabydate_handler = Resource(datastore.DataByDate)
getdatabylocation_handler = Resource(datastore.DataByLocation)

geo_postcode_to_latlng_handler = Resource(geo.PostcodeToLatLng)


# Version 1.0 URLS
urlpatterns = patterns('',

    # Standard Views
    #url(r'^keys$', views.keys, name='keys'),

    #explorer
    url(r'^explorer_call$', views.explorer_user_run, name='explorer_call'),
    url(r'^explorer_example(?P<method>[\w_\-\.\_]+)$', views.explorer_example, name='explorer_example'),

    # Documentation
    url(r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'api/index.html'}),
    url(r'^1\.0$', 'django.views.generic.simple.direct_to_template', {'template': 'api/1.0.html'}, name='index'),
    url(r'^1\.0/libraries$', 'django.views.generic.simple.direct_to_template', {'template': 'api/libraries.html'}, name='libraries'),
    url(r'^1\.0/explore/scraperwiki.scraper.search$', views.explore_scraper_search_1_0, name='scraper_search'),
    url(r'^1\.0/explore/scraperwiki.scraper.getinfo$', views.explore_scraper_getinfo_1_0, name='scraper_getinfo'),    
    url(r'^1\.0/explore/scraperwiki.datastore.getkeys$', views.explore_scraper_getkeys_1_0, name='datastore_getkeys'),    
    url(r'^1\.0/explore/scraperwiki.datastore.search$', views.explore_datastore_search_1_0, name='datastore_search'),        
    url(r'^1\.0/explore/scraperwiki.datastore.getdata$', views.explore_scraper_getdata_1_0, name='scraper_getdata'),    
    url(r'^1\.0/explore/scraperwiki.datastore.getdatabydate$', views.explore_scraper_getdatabydate_1_0, name='scraper_getdatabydate'),
    url(r'^1\.0/explore/scraperwiki.datastore.getdatabylocation$', views.explore_scraper_getdatabylocation_1_0, name='scraper_getdatabylocation'),    
    url(r'^1\.0/explore/scraperwiki.geo.postcodetolatlng$', views.explore_geo_postcodetolatlng_1_0, name='geo_postcodetolatlng'),    

    # API calls

    url(r'^1\.0/scraper/search$', scrapersearch_handler, name="method_search"),
    url(r'^1\.0/scraper/getinfo$', scraperinfo_handler, name="method_getinfo"),
    url(r'^1\.0/datastore/search$', datastore_search_handler, name="method_datastore_search"),
    url(r'^1\.0/datastore/getdata$', data_handler, name="method_getdata"),
    url(r'^1\.0/datastore/getkeys$', keys_handler, name="method_getkeys"),
    url(r'^1\.0/datastore/getdatabydate$', getdatabydate_handler, name="method_getdatabydate"),    
    url(r'^1\.0/datastore/getdatabylocation$', getdatabylocation_handler, name="method_getdatabylocation"),        

    url(r'^1\.0/geo/postcodetolatlng/$', geo_postcode_to_latlng_handler, name="method_geo_postcode_to_latlng"),
    
    
)
