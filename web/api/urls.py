from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from piston.resource import Resource
from handlers import geo
from handlers import scraper
from handlers import datastore

from api import views
from api import viewshandlers


scrapersearch_handler   = Resource(scraper.Search)
scraperinfo_handler     = Resource(scraper.GetInfo)
scraperruninfo_handler  = Resource(scraper.GetRunInfo)
scraperuserinfo_handler = Resource(scraper.GetUserInfo)

data_handler            = Resource(datastore.Data)
keys_handler            = Resource(datastore.Keys)
datastore_search_handler= Resource(datastore.Search)
getdatabydate_handler   = Resource(datastore.DataByDate)
getdatabylocation_handler = Resource(datastore.DataByLocation)
#sqlite_handler          = Resource(datastore.Sqlite)

geo_postcode_to_latlng_handler = Resource(geo.PostcodeToLatLng)


# Version 1.0 URLS
urlpatterns = patterns('',

    # Standard Views
    #url(r'^keys$', views.keys, name='keys'),

    #explorer
    url(r'^explorer_call$',                             views.explorer_user_run,    name='explorer_call'),
    url(r'^explorer_example/(?P<method>[\w_\-\.\_]+)$', views.explorer_example,     name='explorer_example'),
    url(r'^1\.0/libraries$', views.explore_index_1_0_libraries, name='libraries'),

    url(r'^$', 'django.views.generic.simple.redirect_to', {'url': '/docs/api'},name='index'),
    url(r'^1\.0$', 'django.views.generic.simple.redirect_to', {'url': '/docs/api'}, name='index_1_0'),


    url(r'^1\.0/explore/scraperwiki.scraper.search$',       'django.views.generic.simple.redirect_to', {'url': '/docs/api#search'}, name='scraper_search'),
    url(r'^1\.0/explore/scraperwiki.scraper.getinfo$',      'django.views.generic.simple.redirect_to', {'url': '/docs/api#getinfo'},name='scraper_getinfo'),
    url(r'^1\.0/explore/scraperwiki.scraper.getruninfo$',   'django.views.generic.simple.redirect_to', {'url': '/docs/api#getruninfo'},name='scraper_getruninfo'),    
    url(r'^1\.0/explore/scraperwiki.scraper.getuserinfo$',  'django.views.generic.simple.redirect_to', {'url': '/docs/api#getuserinfo'},name='scraper_getuserinfo'),
    url(r'^1\.0/explore/scraperwiki.datastore.sqlite$',     'django.views.generic.simple.redirect_to', {'url': '/docs/api#sqlite'}, name='scraper_sqlite'),    
    
#    url(r'^1\.0/explore/scraperwiki.datastore.getkeys$',    views.explore_scraper_getkeys_1_0,      name='datastore_getkeys'),    
#    url(r'^1\.0/explore/scraperwiki.datastore.search$',     views.explore_datastore_search_1_0,     name='datastore_search'),        
#    url(r'^1\.0/explore/scraperwiki.datastore.getdata$',    views.explore_scraper_getdata_1_0,      name='scraper_getdata'),    
#    url(r'^1\.0/explore/scraperwiki.datastore.getdatabydate$', views.explore_scraper_getdatabydate_1_0, name='scraper_getdatabydate'),
#    url(r'^1\.0/explore/scraperwiki.datastore.getdatabylocation$', views.explore_scraper_getdatabylocation_1_0, name='scraper_getdatabylocation'),    
#    url(r'^1\.0/explore/scraperwiki.geo.postcodetolatlng$', views.explore_geo_postcodetolatlng_1_0, name='geo_postcodetolatlng'),    


    # API calls
    url(r'^1\.0/scraper/search$',       scrapersearch_handler,      name="method_search"),
    url(r'^1\.0/scraper/getinfo$',      scraperinfo_handler,        name="method_getinfo"),
    url(r'^1\.0/scraper/getruninfo$',   scraperruninfo_handler,     name="method_getruninfo"),
    url(r'^1\.0/scraper/getuserinfo$',  scraperuserinfo_handler,    name="method_getuserinfo"),
    
    url(r'^1\.0/datastore/search$',     datastore_search_handler,   name="method_datastore_search"),
    url(r'^1\.0/datastore/getkeys$',    keys_handler,               name="method_getkeys"),
    url(r'^1\.0/datastore/getdatabydate$', getdatabydate_handler,   name="method_getdatabydate"),
    url(r'^1\.0/datastore/getdatabylocation$', getdatabylocation_handler, name="method_getdatabylocation"),
    
    #url(r'^1\.0/datastore/sqlite',      sqlite_handler,             name="method_sqlite"),
    url(r'^1\.0/datastore/sqlite$',     viewshandlers.sqlite_handler,name="method_sqlite"),
    url(r'^1\.0/datastore/getdata$',    viewshandlers.data_handler,  name="method_getdata"),
    url(r'^1\.0/datastore/getolddata$', data_handler,                name="method_getolddata"),

    url(r'^1\.0/geo/postcodetolatlng/$',geo_postcode_to_latlng_handler, name="method_geo_postcode_to_latlng"),
)
