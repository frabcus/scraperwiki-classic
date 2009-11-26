from django.conf.urls.defaults import *

from scraper import views

urlpatterns = patterns('',
                       url(r'^list/$', views.list, name='scraper_list'),
                       url(r'^create/$', views.create, name='scraper_create'),
                       url(r'^show/(?P<scraper_short_name>[\w_\-]+)/$', views.data, name='scraper_data'),
                       url(r'^show/(?P<scraper_short_name>[\w_\-]+)/code/$', views.code, name='scraper_code'),
                       url(r'^show/(?P<scraper_short_name>[\w_\-]+)/contributors/$', views.contributors, name='scraper_contributors'),
                       url(r'^download/(?P<scraper_short_name>[\w_\-]+)/$', views.download, name='scraper_download'),
                       url(r'^export/(?P<scraper_short_name>[\w_\-]+)/$', views.export_csv, name='export_csv'),                       
                       url(r'^tags/$', views.all_tags, name='all_tags'),
                       url(r'^tags/(?P<tag>[\w]+)$', views.tag, name='tag'),
                       url(r'^tags/(?P<tag>[\w]+)/data$', views.tag_data, name='tag_data'),
                       )

