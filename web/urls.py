from django.conf.urls.defaults import *

# please use "import <something> as local_name" as this removes issues of name collision.
import frontend.views as frontend_views

from django.contrib.syndication.views import feed as feed_view
from django.views.generic import date_based, list_detail
from django.views.generic.simple import direct_to_template
from django.contrib import admin
import django.contrib.auth.views as auth_views
from editor import views as editor_views
import settings

from django.contrib import admin
admin.autodiscover()

from frontend.feeds import LatestScrapers, LatestScrapersBySearchTerm, LatestScrapersByTag, CommentsForScraper

feeds = {
    'all_scrapers': LatestScrapers,
    'latest_scrapers_by_search_term': LatestScrapersBySearchTerm,
    'latest_scrapers_by_tag': LatestScrapersByTag,
    'scraper_comments': CommentsForScraper,
}

urlpatterns = patterns('',
    url(r'^$', frontend_views.frontpage, name="frontpage"), 
    url(r'^(?P<wiki_type>scraper|view)s/new/(?P<language>[\w]+)$', editor_views.edit, name="editor"),
    url(r'^(?P<wiki_type>scraper|view)s/(?P<short_name>[\w_\-]+)/edit/$', editor_views.edit, name="editor_edit"),    
    url(r'^', include('codewiki.urls')),    
    url(r'^editor/', include('editor.urls')),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name="logout"), 
    url(r'^accounts/', include('registration.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),
    
    # allows direct viewing of the django tables
    url(r'^admin/(.*)', admin.site.root, name="admin"),

    #paypal
    (r'^paypal/notifications/56db6e2700d04e38a5d/', include('paypal.standard.ipn.urls')),
    
    # market place
    url(r'^market/', include('market.urls')),
    
    # favicon
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),

    # RSS feeds  
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

    # API
    (r'^api/', include('api.urls', namespace='foo', app_name='api')),

    # Robots.txt
    (r'^robots.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),

    # Key Performance Indicators
    (r'^kpi/', include('kpi.urls')),
    
    # Black/Whitelist management
    (r'^whitelist/', include('whitelist.urls')),
    
    # static media server for the dev sites / local dev
    url(r'^media/(?P<path>.*)$',       'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ADMIN_DIR, 'show_indexes':True}),

    #Rest of the site
    url(r'^', include('frontend.urls')),
)
