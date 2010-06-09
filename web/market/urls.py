from django.conf.urls.defaults import *
from market import views

urlpatterns = patterns('',
   url(r'^$', views.market_list, name="market_list"),
   url(r'^(?P<mode>completed|pending)/$', views.market_list, name="market_list_filter"),
   url(r'^request/$', views.request_solicitation, name='market_solicitation'),
   url(r'^view/(?P<solicitation_id>\d+)/$', views.single, name='market_view'),
   url(r'^edit/(?P<solicitation_id>\d+)/$', views.edit, name='market_edit'),
   url(r'^claim/(?P<solicitation_id>\d+)/$', views.claim, name='market_claim'),
   url(r'^complete/(?P<solicitation_id>\d+)/$', views.complete, name='market_complete'),
   url(r'^payment/return/$', views.paypal_return, name='market_paypal_return'),
   url(r'^payment/cancel/$', views.paypal_cancel, name='market_paypal_cancel'),   
   url(r'^tags/(?P<tag>[\w]+)$', views.tag, name='market_tag'),                                           
   )
