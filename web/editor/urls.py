from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
  url(r'^$', views.edit, name="editor"),
  url(r'^(?P<short_name>[\-\w]+)$', views.edit, name="editor"),
  
)