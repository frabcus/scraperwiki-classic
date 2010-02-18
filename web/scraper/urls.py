from django.conf.urls.defaults import *

from scraper import views

urlpatterns = patterns('',
   url(r'^list/$', views.scraper_list, name='scraper_list'),
   url(r'^create/$', views.create, name='scraper_create'),
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/$', views.overview, name='scraper_overview'),
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/map/$', views.scraper_map, name='scraper_map'),                                              
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/data/$', views.scraper_data, name='scraper_data'),                       
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/code/$', views.code, name='scraper_code'),
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/history/$', views.scraper_history, name='scraper_history'),
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/contributors/$', views.contributors, name='scraper_contributors'),
   url(r'^show/(?P<scraper_short_name>[\w_\-]+)/comments/$', views.comments, name='scraper_comments'),
   url(r'^download/(?P<scraper_short_name>[\w_\-]+)/$', views.download, name='scraper_download'),
   url(r'^export/(?P<scraper_short_name>[\w_\-]+)/$', views.export_csv, name='export_csv'),                       
   url(r'^tags/$', views.all_tags, name='all_tags'),
   url(r'^tags/(?P<tag>[\w]+)$', views.scraper_tag, name='tag'),
   url(r'^tags/(?P<tag>[\w]+)/data$', views.tag_data, name='tag_data'),  # to delete
   url(r'^search/$', views.search, name='search'),
   url(r'^search/(?P<q>.+)/$', views.search, name='search'),
   url(r'^follow/(?P<scraper_short_name>[\w_\-]+)/$', views.follow, name='scraper_follow'),
   url(r'^unfollow/(?P<scraper_short_name>[\w_\-]+)/$', views.unfollow, name='scraper_unfollow'),                   
)

