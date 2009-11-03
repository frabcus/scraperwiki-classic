from django.conf.urls.defaults import *
from market import views

urlpatterns = patterns('',
                       url(r'^list/$', views.list, name='market_list'),
                       url(r'^request/$', views.solicitation, name='market_solicitation'),)