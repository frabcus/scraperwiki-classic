from django.conf.urls.defaults import *

from codewiki import views, viewsrpc, viewsuml, viewseditor

from django.conf.urls.defaults import *
from piston.resource import Resource

from handlers import ScraperMetadataHandler

metadata = Resource(handler=ScraperMetadataHandler)

urlpatterns = patterns('',
    
    # use this to monitor the site
    url(r'^table/$',                                      views.scraper_table,          name='scraper_table'),

    # special views functionality
    url(r'^run/(?P<short_name>[\w_\-]+)/(?P<revision>\d+/)?$', 
                                                          viewsrpc.rpcexecute,          name='rpcexecute'),    
    url(r'^views/(?P<short_name>[\w_\-]+)/html/$',        views.htmlview,               name='htmlview'),
    url(r'^views/(?P<short_name>[\w_\-]+)/full/$',        views.view_fullscreen,        name='view_fullscreen'),   
    url(r'^views/(?P<short_name>[\w_\-]+)/admin/$',       views.view_admin,             name='view_admin'),    
    
    url(r'^scrapers/delete-data/(?P<short_name>[\w_\-]+)/$', views.scraper_delete_data, name='scraper_delete_data'),
    url(r'^scrapers/export/(?P<short_name>[\w_\-]+)/$',   views.export_csv,             name='export_csv'),
    url(r'^scrapers/export2/(?P<short_name>[\w_\-]+)/$',  views.export_gdocs_spreadsheet,name='export_gdocs_spreadsheet'),    
    
    url(r'^scrapers/follow/(?P<short_name>[\w_\-]+)/$',   views.follow,                 name='scraper_follow'),
    url(r'^scrapers/unfollow/(?P<short_name>[\w_\-]+)/$', views.unfollow,               name='scraper_unfollow'),
    
    url('^(?P<scraper_guid>[\w_\-]+)/(?P<metadata_name>.+)/$', metadata, name='metadata_api'),

    # events and monitoring (pehaps should have both wiki_types possible)
    url(r'^scrapers/running_scrapers/$',                  viewsuml.running_scrapers,    name='running_scrapers'),
    
    url(r'^scrapers/run/(?P<run_id>[\w_\-\.\?]+)/$',      viewsuml.run_event,           name='run_event'),  # the ? is due to the temporary holding value in older objects and should be cleared  out
    
    url(r'^scrapers/scraper_killrunning/(?P<run_id>[\w_\-\.]+)(?:/(?P<event_id>[\w_\-]+))?$',
                                                          viewsuml.scraper_killrunning, name='scraper_killrunning'),
        
    url(r'^scrapers/schedule-scraper/(?P<short_name>[\w_\-]+)/$', 
                                                          views.scraper_schedule_scraper,name='scraper_schedule_scraper'),
    url(r'^(?P<wiki_type>scraper|view)s/delete-scraper/(?P<short_name>[\w_\-]+)/$', 
                                                          views.scraper_delete_scraper, name='scraper_delete_scraper'),
    url(r'^scrapers/run-scraper/(?P<short_name>[\w_\-]+)/$', 
                                                          views.scraper_run_scraper,    name='scraper_run_scraper'),
    url(r'^(?P<wiki_type>scraper|view)s/screenshoot-scraper/(?P<short_name>[\w_\-]+)/$', 
                                                          views.scraper_screenshoot_scraper,    name='scraper_screenshoot_scraper'),
        #not deprecated as used in by ajax to implement publishScraperButton
    url(r'^scrapers/(?P<short_name>[\w_\-]+)/admin/$',    views.scraper_admin,          name='scraper_admin'),
        
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/$',          views.code_overview,    name='code_overview'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/history/$',  views.scraper_history,  name='scraper_history'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/comments/$', views.comments,         name='scraper_comments'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/code/$',     viewseditor.code,       name='scraper_code'),    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/tags/$',     views.tags,             name='scraper_tags'),    
        
    url(r'^(?P<wiki_type>scraper|view)s/new/choose_template/$',               views.choose_template, name='choose_template'),    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/raw_about_markup/$', views.raw_about_markup, name='raw_about_markup'),        
    
        # redirects to new scraper?template=
    url(r'^editor/template/(?P<short_name>[\-\w]+)$',     viewseditor.edittutorial, name="tutorial"),  

    # call-backs from ajax for reloading and diff
    url(r'^editor/draft/delete/$',                        views.delete_draft, name="delete_draft"),
    url(r'^editor/diff/(?P<short_name>[\-\w]*)$',         viewseditor.diff,   name="diff"),
    url(r'^editor/raw/(?P<short_name>[\-\w]*)$',          viewseditor.raw,    name="raw"),   # blank name for draft scraper
    url(r'^proxycached$',                                 views.proxycached,  name="proxycached"), 
    
    # editor (the action stuff is deprecated)
    url(r'^handle_session_draft/$',                       viewseditor.handle_session_draft, name="handle_session_draft"),
    url(r'^handle_editor_save/$',                         viewseditor.handle_editor_save,   name="handle_editor_save"),    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/edit/$',     viewseditor.edit, name="editor_edit"),    
    url(r'^(?P<wiki_type>scraper|view)s/new/(?P<language>[\w]+)$',            viewseditor.edit, name="editor"),
)
