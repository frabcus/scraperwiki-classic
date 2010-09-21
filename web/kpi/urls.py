from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    url(r'^$',          views.index),
    url(r'^umlstatus$', views.umlstatus,     name='umlstatus'),
)
