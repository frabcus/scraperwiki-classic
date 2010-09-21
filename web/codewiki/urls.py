from django.conf.urls.defaults import *

from codewiki import views, viewsrpc

urlpatterns = patterns('',
    
    # use this to monitor the site
    url(r'^table/$',                                      views.scraper_table,          name='scraper_table'),

    # special views functionality
    url(r'^views/(?P<scraper_short_name>[\w_\-]+)/run/(?P<revision>\d+/)?$', 
                                                          viewsrpc.rpcexecute,          name='rpcexecute'),    
    url(r'^views/(?P<scraper_short_name>[\w_\-]+)/html/$',views.htmlview,               name='htmlview'),
    url(r'^views/(?P<short_name>[\w_\-]+)/full/$',        views.view_fullscreen,        name='view_fullscreen'),   
    url(r'^views/(?P<short_name>[\w_\-]+)/admin/$',       views.view_admin,             name='view_admin'),    
    
    url(r'^scrapers/delete-data/(?P<scraper_short_name>[\w_\-]+)/$', views.scraper_delete_data, name='scraper_delete_data'),
    url(r'^scrapers/download/(?P<scraper_short_name>[\w_\-]+)/$', views.download,       name='scraper_download'),
    url(r'^scrapers/export/(?P<scraper_short_name>[\w_\-]+)/$', views.export_csv,       name='export_csv'),
    
    url(r'^scrapers/tags/$',                              views.all_tags,               name='all_tags'),
    url(r'^scrapers/tags/(?P<tag>[^/]+)$',                views.scraper_tag,            name='tag'),
    url(r'^scrapers/tags/(?P<tag>[^/]+)/data$',           views.tag_data,               name='tag_data'),  # to delete
    url(r'^scrapers/follow/(?P<scraper_short_name>[\w_\-]+)/$', views.follow,           name='scraper_follow'),
    url(r'^scrapers/unfollow/(?P<scraper_short_name>[\w_\-]+)/$', views.unfollow,       name='scraper_unfollow'),
    
    url(r'^scrapers/metadata_api/', include('codewiki.metadata_api.urls')),

    # events and monitoring (pehaps should have both wiki_types possible)
    url(r'^scrapers/run/(?P<event_id>[\w_\-]+)/$',        views.run_event,              name='run_event'),
    url(r'^scrapers/commit/(?P<event_id>\d+)/$',          views.commit_event,           name='commit_event'),
    url(r'^scrapers/running_scrapers/$',                  views.running_scrapers,       name='running_scrapers'),
    url(r'^scrapers/schedule-scraper/(?P<scraper_short_name>[\w_\-]+)/$', 
                                                          views.scraper_schedule_scraper,name='scraper_schedule_scraper'),
    url(r'^scrapers/delete-scraper/(?P<scraper_short_name>[\w_\-]+)/$', 
                                                          views.scraper_delete_scraper, name='scraper_delete_scraper'),
    url(r'^scrapers/run-scraper/(?P<scraper_short_name>[\w_\-]+)/$', 
                                                          views.scraper_run_scraper,    name='scraper_run_scraper'),
    
    url(r'^scrapers/twister/status$', views.twisterstatus, name='twisterstatus'),
        
        #not deprecated as used in by ajax to implement publishScraperButton
    url(r'^scrapers/(?P<short_name>[\w_\-]+)/admin/$',    views.scraper_admin,          name='scraper_admin'),
        
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/$',          views.code_overview,    name='code_overview'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/history/$',  views.scraper_history,  name='scraper_history'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/comments/$', views.comments,         name='scraper_comments'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/code/$',     views.code,             name='scraper_code'),    
        
    url(r'^(?P<wiki_type>scraper|view)s/new/choose_template/$', views.choose_template, name='choose_template'),    
    url(r'^(?P<wiki_type>scraper|view)s/new/chosen_template/$', views.chosen_template, name='chosen_template'),      # NB not duplicate
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/raw_about_markup/$', views.raw_about_markup, name='raw_about_markup'),        
    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/edit/$', views.edit, name="editor_edit"),    
    
    # both of these methods lead to pre-populating a new draft scraper with code copied from another scraper 
    # (the former with a field ?template=name which I far prefer because it doesn't lead to a misleading url.
    #  use the 'ugly' ?= version; beauty is not always truth)
    url(r'^(?P<wiki_type>scraper|view)s/new/(?P<language>[\w]+)$',  views.edit, name="editor"),
    url(r'^editor/template/(?P<tutorial_scraper>[\-\w]+)$',         views.edit, name="tutorial"),

    url(r'^handle_session_draft/(?P<action>[\-\w]+)$',              views.handle_session_draft, name="handle_session_draft"),
    
    # call-backs from ajax for reloading and diff
    url(r'^editor/draft/delete/$',                             views.delete_draft, name="delete_draft"),
    url(r'^editor/diff/(?P<short_name>[\-\w]*)$',              views.diff,         name="diff"),
    url(r'^editor/raw/(?P<short_name>[\-\w]*)$',               views.raw,          name="raw"),   # blank name for draft scraper

    
)
