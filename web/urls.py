from django.conf.urls.defaults import *

# please use "import <something> as local_name" as this removes issues of name collision.
import frontend.views as frontend_views

from django.contrib.syndication.views import feed as feed_view
from django.views.generic import date_based, list_detail
from django.views.generic.simple import direct_to_template
from django.contrib import admin
import django.contrib.auth.views as auth_views
import settings

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from django.contrib import admin
admin.autodiscover()

from frontend.feeds import LatestCodeObjects, LatestCodeObjectsBySearchTerm, LatestCodeObjectsByTag, CommentsForCode

feeds = {
    'all_code_objects': LatestCodeObjects,
    'latest_code_objects_by_search_term': LatestCodeObjectsBySearchTerm,
    'latest_code_objects_by_tag': LatestCodeObjectsByTag,
    'code_object_comments': CommentsForCode,
}

urlpatterns = patterns('',
    url(r'^$', frontend_views.frontpage, name="frontpage"), 
    
    # redirects from old version (would clashes if you happen to have a scraper whose name is list!)
    (r'^scrapers/list/$', lambda request: HttpResponseRedirect(reverse('scraper_list_wiki_type', args=['scraper']))),

    url(r'^', include('codewiki.urls')),    
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name="logout"), 
    url(r'^accounts/', include('registration.urls')),
    url(r'^accounts/resend_activation_email/', frontend_views.resend_activation_email, name="resend_activation_email"),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^captcha/', include('captcha.urls')),
    
    # allows direct viewing of the django tables
    url(r'^admin/(.*)', admin.site.root, name="admin"),

    #paypal
    (r'^paypal/notifications/56db6e2700d04e38a5d/', include('paypal.standard.ipn.urls')),
    
    # market place
    url(r'^market/', include('market.urls')),

    # favicon
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),

    # RSS feeds  
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name='feeds'),

    # API
    (r'^api/', include('api.urls', namespace='foo', app_name='api')),

    # Robots.txt
    (r'^robots.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),

    # Key Performance Indicators
    (r'^kpi/', include('kpi.urls')),
    
    # Black/Whitelist management
    (r'^whitelist/', include('whitelist.urls')),
    
    # pdf cropper technology
    (r'^cropper/', include('cropper.urls')),
    
    # static media server for the dev sites / local dev
    url(r'^media/(?P<path>.*)$',       'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ADMIN_DIR, 'show_indexes':True}),

    #Rest of the site
    url(r'^', include('frontend.urls')),

    # redirects from old version
    (r'^editor/$', lambda request: HttpResponseRedirect('/editor/template/tutorial-1')),
    (r'^scrapers/show/(?P<short_name>[\w_\-]+)/(?:data/|map-only/)?$', 
                   lambda request, short_name: HttpResponseRedirect(reverse('code_overview', args=['scraper', short_name]))),
#    http://scraperwiki.com/scrapers/epsrc-grants-1/
    
)
