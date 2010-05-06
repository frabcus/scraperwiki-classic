from django.conf.urls.defaults import *
from whitelist import views

urlpatterns = patterns('',
   url(r'^$',      views.whitelist_user, name="whitelist_user"),
   url(r'^config$', views.whitelist_config, name="whitelist_config"),
   )
