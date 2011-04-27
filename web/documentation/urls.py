from django.conf.urls.defaults import *
from documentation import views

urlpatterns = patterns('',
   url(r'^$', views.catchall, name="docsroot"),
#   url(r'^contrib/(?P<path>.+)/$', views.contribs, name="contrib"),
   url(r'^(?P<path>.+)/$', views.catchall, name="docs"),
)
