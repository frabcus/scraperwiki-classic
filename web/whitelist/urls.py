from django.conf.urls.defaults import *
from whitelist import views

urlpatterns = patterns('',
   url(r'^$',      views.whitelist_user, name="whitelist_user"),
   url(r'^white$', views.whitelist_white, name="whitelist_white"),
   url(r'^black$', views.whitelist_black, name="whitelist_black"),
    # room for more colours here
   )