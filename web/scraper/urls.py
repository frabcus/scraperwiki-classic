from django.conf.urls.defaults import *

from scraper import views

urlpatterns = patterns('',
                       url(r'^list/$', views.list, name='scraper_list'),
                       url(r'^create/$', views.create, name='scraper_create'),
                       url(r'^show/(?P<scraper_short_name>[\w_\-]+)/$', views.data, name='scraper_data'),
                       url(r'^show/(?P<scraper_short_name>[\w_\-]+)/code/$', views.code, name='scraper_code'),                           
                       url(r'^download/(?P<scraper_id>[\w_\-]+)$', views.download, name='scraper_download'),
                       url(r'^request/$', views.scraper_request, name='scraper_request'),)

