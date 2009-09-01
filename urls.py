from django.conf.urls.defaults import *

import codewiki.views_code as views_code
import codewiki.views_main as views_main

from django.contrib.syndication.views import feed as feed_view
from django.views.generic import date_based, list_detail
from django.contrib import admin
from blog.models import Entry

import settings

from django.contrib import admin
admin.autodiscover()

info_dict = {
    'queryset': Entry.objects.order_by('pub_date'),
    'date_field': 'pub_date',
}



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

    url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>\w+)/$', date_based.object_detail, dict(info_dict, slug_field='slug')),
    url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$', date_based.archive_day, info_dict),
    url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$', date_based.archive_month, info_dict),
    url(r'^     (?P<year>\d{4})/$', date_based.archive_year, info_dict),
    url(r'^archives/', list_detail.object_list, {'queryset': Entry.objects.order_by('-pub_date'), 'template_name': 'blog/archive.html'}),
    url(r'^blog/', date_based.archive_index, dict(info_dict, template_name='homepage.html')),

    # these ought to be implemented by the webserver
    url(r'^media/(?P<path>.*)$',       'django.views.static.serve', {'document_root': settings.MEDIA_DIR, 'show_indexes':True}),
    url(r'^media-admin/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ADMIN_DIR, 'show_indexes':True}),
    
    # allows direct viewing of the django tables
    url(r'^admin/(.*)', admin.site.root, name="admin"),
)

