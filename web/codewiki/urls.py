from django.conf.urls.defaults import *

from codewiki import views, viewsrpc, viewsuml, viewseditor

from django.conf.urls.defaults import *
from piston.resource import Resource

from handlers import ScraperMetadataHandler
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings


metadata = Resource(handler=ScraperMetadataHandler)

urlpatterns = patterns('',
    
    # running a scraper by calling a url (from scraperwikiviews.com)
    url(r'^run/(?P<short_name>[\w_\-\.]+)/(?:(?P<revision>\d+)/)?$', 
                                                          viewsrpc.rpcexecute,          name='rpcexecute'),    

    url(r'^views/(?P<short_name>[\w_\-\.]+)/admin/$',     views.view_admin,             name='view_admin'),    
    
    url(r'^scrapers/delete-data/(?P<short_name>[\w_\-\.]+)/$', views.scraper_delete_data, name='scraper_delete_data'),
    url(r'^scrapers/converttosqlitedatastore/(?P<short_name>[\w_\-\.]+)/$', views.scraper_converttosqlitedatastore, name='scraper_converttosqlitedatastore'),
            
    url(r'^scrapers/export/(?P<short_name>[\w_\-\.]+)/$', views.export_csv,             name='export_csv'),
    url(r'^scrapers/export_sqlite/(?P<short_name>[\w_\-\.]+)/$',  views.export_sqlite,          name='export_sqlite'),
    
    url(r'^scrapers/follow/(?P<short_name>[\w_\-\.]+)/$',   views.follow,               name='scraper_follow'),
    url(r'^scrapers/unfollow/(?P<short_name>[\w_\-\.]+)/$', views.unfollow,             name='scraper_unfollow'),
    
    url(r'^scrapers/metadata_api/(?P<scraper_guid>[\w_\-\.]+)/(?P<metadata_name>.+)/$', metadata, name='metadata_api'),

    # events and monitoring (pehaps should have both wiki_types possible)
    url(r'^scrapers/running_scrapers/$',                  viewsuml.running_scrapers,    name='running_scrapers'),
    
    url(r'^scrapers/scraper_killrunning/(?P<run_id>[\w_\-\.\|]+)(?:/(?P<event_id>[\w_\-]+))?$',
                                                          viewsuml.scraper_killrunning, name='scraper_killrunning'),
        
    url(r'^scrapers/schedule-scraper/(?P<short_name>[\w_\-\.]+)/$', 
                                                          views.scraper_schedule_scraper,name='scraper_schedule_scraper'),
    url(r'^(?P<wiki_type>scraper|view)s/delete-scraper/(?P<short_name>[\w_\-\.]+)/$', 
                                                          views.scraper_delete_scraper, name='scraper_delete_scraper'),
    url(r'^scrapers/run-scraper/(?P<short_name>[\w_\-\.]+)/$', 
                                                          views.scraper_run_scraper,    name='scraper_run_scraper'),
    url(r'^(?P<wiki_type>scraper|view)s/screenshoot-scraper/(?P<short_name>[\w_\-\.]+)/$', 
                                                          views.scraper_screenshoot_scraper,    name='scraper_screenshoot_scraper'),
        
        #not deprecated as used in by ajax to implement publishScraperButton
    url(r'^scrapers/(?P<short_name>[\w_\-\.]+)/admin/$',  views.scraper_admin,          name='scraper_admin'),
        
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/$',          views.code_overview,    name='code_overview'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/history/$',  views.scraper_history,  name='scraper_history'),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/comments/$', views.comments,         name='scraper_comments'),
    
    
    url(r'^scrapers/run_event/(?P<run_id>[\w_\-\.\?]+)/$',                      viewsuml.run_event,     name='run_event'),  # the \? is due to the temporary holding value in older objects and should be cleared  out
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/tags/$',     views.tags,             name='scraper_tags'),    
        
    url(r'^(?P<wiki_type>scraper|view)s/new/choose_template/$',                 views.choose_template,  name='choose_template'),    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/raw_about_markup/$', views.raw_about_markup, name='raw_about_markup'),        
    
    url(r'^editor/draft/delete/$',                        views.delete_draft, name="delete_draft"),
    
    # call-backs from ajax for reloading and diff
    url(r'^editor/raw/(?P<short_name>[\-\w\.]+)$',        viewseditor.raw,    name="raw"),      # raw code not wrapped in javascript
    url(r'^editor/diffseq/(?P<short_name>[\-\w\.]+)$',    viewseditor.diffseq,name="diffseq"),
    url(r'^scrapers/run_event_json/(?P<run_id>[\w_\-\.\?]+)/$', viewseditor.run_event_json, name='run_event_json'),  
    
    url(r'^editor/reload/(?P<short_name>[\-\w\.]+)$',     viewseditor.reload, name="reload"),   
    url(r'^proxycached$',                                 views.proxycached,  name="proxycached"), # ?cachedid=1234
    url(r'^editor/quickhelp$',                            viewseditor.quickhelp, name="quickhelp"), # ?language&wiki_type&line&character

    # editor 
    url(r'^handle_session_draft/$',                       viewseditor.handle_session_draft, name="handle_session_draft"),
    url(r'^handle_editor_save/$',                         viewseditor.handle_editor_save,   name="handle_editor_save"),    
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/edit/$',   viewseditor.edit, name="editor_edit"),
    url(r'^(?P<wiki_type>scraper|view)s/new/(?P<language>[\w]+)$',            viewseditor.edit, name="editor"),


    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-\.]+)/(?:run|full)/$',   # redirect because it's so common
                   lambda request, wiki_type, short_name: HttpResponseRedirect("http://%s%s" % (settings.VIEW_DOMAIN, reverse('rpcexecute', args=[short_name])))),
    url(r'^(?P<wiki_type>scraper)s/export2/(?P<short_name>[\w_\-\.]+)/$', 
                   lambda request, wiki_type, short_name: HttpResponseRedirect(reverse('code_overview', args=[wiki_type, short_name]))),
    #url(r'^(?P<wiki_type>scraper)s/export/(?P<short_name>[\w_\-\.]+)/$', 
    #               lambda request, wiki_type, short_name: HttpResponseRedirect(reverse('code_overview', args=[wiki_type, short_name]))),

)

