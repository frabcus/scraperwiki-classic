from django.conf.urls.defaults import *

import codewiki.views_code as views_code
import codewiki.views_main as views_main

import settings

from django.contrib import admin
admin.autodiscover()

# sort out clash between from django.db import models and codewiki.models
# collectors should make django tables (difficult) under development
# move hungary and pdf handling from farmsubsidy/
# remove all log files references


urlpatterns = patterns('',
    url(r'^$', views_main.frontpage, name="frontpage"), 

    url(r'^(?P<dirname>(?:readers|detectors|collectors|observers))(?:/(?P<subdirname>.+?))?/$', views_code.codewikidir,  name="codewikidir"),
    url(r'^(?P<dirname>(?:readers|detectors|collectors|observers))/(?P<filename>.+?\.py)$',     views_code.codewikipage, name="codewikifile"),
    url(r'^reading/(?P<pageid>\d+)$',                                views_code.readingeditpageid, name="readingedit"),
    url(r'^reading/(?P<pageid>\d+)(?P<fileext>\.html|\.pdf|\.xml)$', views_code.readingrawpageid,  name="readingraw"),
    url(r'^readings/$',                                              views_code.readingsall,       name="readingsall"),
    url(r'^observation/(?P<observername>.+?)/(?:(?P<tail>.+?))?$',   views_main.observer,          name="observer"), 

    # these ought to be implemented by the webserver
    url(r'^media/(?P<path>.*)$',       'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ADMIN_DIR, 'show_indexes':True}),
    
    # allows direct viewing of the django tables
    url(r'^admin/(.*)', admin.site.root, name="admin"),
)

