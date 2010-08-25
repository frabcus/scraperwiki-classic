from django.conf.urls.defaults import *

from codewiki import views

urlpatterns = patterns('',
    url(r'^table/$', views.scraper_table, name='scraper_table'),

    url(r'^scrapers/(?P<scraper_short_name>[\w_\-]+)/$',        views.scraper_overview,                 name='scraper_overview'),
    url(r'^scrapers/(?P<scraper_short_name>[\w_\-]+)/map/$',    views.scraper_map, {'map_only': False}, name='scraper_map'),
    url(r'^scrapers/(?P<scraper_short_name>[\w_\-]+)/map-only/$',views.scraper_map, {'map_only': True}, name='scraper_map_only'),
    url(r'^scrapers/(?P<short_name>[\w_\-]+)/admin/$',  views.scraper_admin,            name='scraper_admin'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<scraper_short_name>[\w_\-]+)/history/$',views.scraper_history,          name='scraper_history'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<scraper_short_name>[\w_\-]+)/comments/$',views.comments,                name='scraper_comments'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<scraper_short_name>[\w_\-]+)/code/$',views.code,          name='scraper_code'),    

    url(r'^scrapers/delete-data/(?P<scraper_short_name>[\w_\-]+)/$', views.scraper_delete_data, name='scraper_delete_data'),
    url(r'^scrapers/delete-scraper/(?P<scraper_short_name>[\w_\-]+)/$', views.scraper_delete_scraper, name='scraper_delete_scraper'),
    url(r'^scrapers/download/(?P<scraper_short_name>[\w_\-]+)/$', views.download, name='scraper_download'),
    url(r'^scrapers/export/(?P<scraper_short_name>[\w_\-]+)/$', views.export_csv, name='export_csv'),
    url(r'^scrapers/tags/$', views.all_tags, name='all_tags'),
    url(r'^scrapers/tags/(?P<tag>[^/]+)$', views.scraper_tag, name='tag'),
    url(r'^scrapers/tags/(?P<tag>[^/]+)/data$', views.tag_data, name='tag_data'),  # to delete
    url(r'^scrapers/follow/(?P<scraper_short_name>[\w_\-]+)/$', views.follow, name='scraper_follow'),
    url(r'^scrapers/unfollow/(?P<scraper_short_name>[\w_\-]+)/$', views.unfollow, name='scraper_unfollow'),
    url(r'^scrapers/twister/status$', views.twisterstatus, name='twisterstatus'),

    url(r'^views/(?P<short_name>[\w_\-]+)/$',        views.view_overview,                 name='view_overview'),
    url(r'^views/(?P<scraper_short_name>[\w_\-]+)/run/$', views.rpcexecute_dummy, name='rpcexecute'),
    url(r'^views/(?P<scraper_short_name>[\w_\-]+)/run/(?P<revision>\d+)/$', views.rpcexecute_dummy, name='rpcexecute'),    
    url(r'^views/(?P<scraper_short_name>[\w_\-]+)/html/$',       views.htmlview,   name='htmlview'),
    url(r'^views/(?P<short_name>[\w_\-]+)/full/$',        views.view_fullscreen,                 name='view_fullscreen'),   

    url(r'^scrapers/metadata_api/', include('codewiki.metadata_api.urls')),

    url(r'^scrapers/run/(?P<event_id>[\w_\-]+)/$', views.run_event, name='run_event'),
    url(r'^scrapers/commit/(?P<event_id>\d+)/$', views.commit_event, name='commit_event'),
    url(r'^scrapers/running_scrapers/$', views.running_scrapers, name='running_scrapers'),

    url(r'^(?P<wiki_type>scraper|view)s/new/choose_template/$', views.choose_template, name='choose_template'),    
    url(r'^(?P<wiki_type>scraper|view)s/new/chosen_template/$', views.chosen_template, name='chosen_template'),        
    url(r'^ajax/ajax_update_codewiki_details/$', views.ajax_update_codewiki_details, name='ajax_update_codewiki_details'),            
)
