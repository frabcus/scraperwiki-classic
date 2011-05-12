from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from piston.resource import Resource

from handlers import scraper

from api import views
from api import viewshandlers
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

try:    import json
except: import simplejson as json


# Version 1.0 URLS
urlpatterns = patterns('',
    # current api
    url(r'^1\.0/datastore/sqlite$',     viewshandlers.sqlite_handler,name="method_sqlite"),
    url(r'^1\.0/datastore/getdata$',    viewshandlers.data_handler,  name="method_getdata"),
    url(r'^1\.0/scraper/search$',       viewshandlers.scraper_search_handler,      name="method_search"),
    url(r'^1\.0/scraper/getuserinfo$',  viewshandlers.userinfo_handler,    name="method_getuserinfo"),
    
    url(r'^1\.0/scraper/getruninfo$',   viewshandlers.runevent_handler,     name="method_getruninfo"),
    url(r'^1\.0/scraper/getinfo$',      viewshandlers.scraperinfo_handler,        name="method_getinfo"),

    # deprecated api
    url(r'^1\.0/datastore/search$', lambda request: HttpResponse(json.dumps({ "error":"Sorry, this function has been deprecated.", "message":"no search is possible across different databases" }))),
    url(r'^1\.0/datastore/getkeys$', lambda request: HttpResponse(json.dumps({ "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with format=jsonlist and limit 0" }))),
    url(r'^1\.0/datastore/getdatabydate$', lambda request: HttpResponse(json.dumps({ "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with bounds on your date field" }))),
    url(r'^1\.0/datastore/getdatabylocation$', lambda request: HttpResponse(json.dumps({ "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite bounds on the lat lng values" }))),
    url(r'^1\.0/geo/postcodetolatlng/$', lambda request: HttpResponse(json.dumps({ "error":"Sorry, this function has been deprecated.", "message":"use the scraperwiki postcode view to do it" }))),

    
    # explorer redirects
    url(r'^1\.0/explore/scraperwiki.(?:scraper|datastore).(?P<shash>\w+)$', 
                   lambda request, shash: HttpResponseRedirect("%s#%s" % (reverse('docsexternal'), shash))),
    
    #explorer
    url(r'^explorer_call$',                             views.explorer_user_run,    name='explorer_call'),
    url(r'^explorer_example/(?P<method>[\w_\-\.\_]+)$', views.explorer_example,     name='explorer_example'),

    url(r'^$', 'django.views.generic.simple.redirect_to', {'url': '/docs/api'},name='index'),
    url(r'^1\.0$', 'django.views.generic.simple.redirect_to', {'url': '/docs/api'}, name='index_1_0'),


)
