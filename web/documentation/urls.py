from django.conf.urls.defaults import *
from documentation import views

urlpatterns = patterns('',
   url(r'^$', views.catchall, name="documentation"),
   url(r'^(?P<path>.+)/$', views.catchall),
)
