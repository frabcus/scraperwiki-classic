from django.conf.urls.defaults import *

from codewiki.views_code import *
from codewiki.views_scope import *
from codewiki.views_api import *

import codewiki.views_code as views_code
import codewiki.views_scope as views_scope
import codewiki.views_api as views_api


import settings

from django.contrib import admin
admin.autodiscover()

# change ScrapedText to Reading and make it retrieve the data directly from the file instead of storing it
# collectors should make django tables (difficult)
# move hungary and pdf handling from farmsubsidy/
# remove all log files references


urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root, name="admin"),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ADMIN, 'show_indexes':True}),
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    url(r'^$', views_scope.scopeindex, name="index"), 

    url(r'^(?P<dirname>(?:readers|detectors|collectors|observers))(?:/(?P<subdirname>.+?))?/$', views_code.codewikidir,  name="codewikidir"),
    url(r'^(?P<dirname>(?:readers|detectors|collectors|observers))/(?P<filename>.+?\.py)$',     views_code.codewikipage, name="codewikifile"),
    url(r'^reading/(?P<pageid>\d+)$',                           views_code.readingeditpageid, name="readingedit"),
    url(r'^reading/(?P<pageid>\d+)(?P<fileext>\.html|\.pdf|\.xml)$',    views_code.readingrawpageid,  name="readingraw"),
    url(r'^readings/$', views_code.readingsall, name="readingsall"),
    url(r'^observation/(?P<observername>.+?)(?:/(?P<tail>.+?))?$', views_api.observer,           name="observer"), 
)

