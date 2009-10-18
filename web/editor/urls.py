from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
  url(r'^$', views.edit, name="editor"),
  url(r'^/(?P<scraper_id>\d+)$', views.edit, name="editor"),
  
)