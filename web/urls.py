from django.conf.urls.defaults import *


# please use "import <something> as local_name" as this removes issues of name collision.
import frontend.views as frontend_views

from django.contrib.syndication.views import feed as feed_view
from django.views.generic import date_based, list_detail
from django.contrib import admin
import django.contrib.auth.views as auth_views

import settings

from django.contrib import admin
admin.autodiscover()


# sort out clash between from django.db import models and codewiki.models
# collectors should make django tables (difficult) under development
# move hungary and pdf handling from farmsubsidy/
# remove all log files references


urlpatterns = patterns('',
    url(r'^profiles/', include('profiles.urls')),
    url(r'^$', frontend_views.frontpage, name="frontpage"), 
    url(r'^', include('frontend.urls')),
    url(r'^editor/', include('editor.urls')),
    
    
    url(r'^scraper_data/(?P<short_name>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}, name="scraper_data"),
    
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name="logout"), 
    url(r'^accounts/', include('registration.urls')),
    url(r'^scrapers/', include('scraper.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),

    # these ought to be implemented by the webserver
    url(r'^media/(?P<path>.*)$',       'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ADMIN_DIR, 'show_indexes':True}),
    
    # allows direct viewing of the django tables
    url(r'^admin/(.*)', admin.site.root, name="admin"),
    
)
