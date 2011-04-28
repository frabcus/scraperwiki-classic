from django.conf.urls.defaults import *
from documentation import views

urlpatterns = patterns('',
   url(r'^$',                               views.docmain,      name="docsroot"),
   url(r'^api_explorer___$',                views.api_explorer, name="api_explore"),
   url(r'^api$',                            views.docexternal,  name="docsexternal"),
   url(r'^contrib/(?P<short_name>[\w_\-\./]+)/$', views.contrib,name="docscontrib"),
   url(r'^(?P<path>[\w_\-\.]+)/$',          views.docmain,      name="docs"),
)
