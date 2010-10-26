from django.conf.urls.defaults import patterns, url
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import cropper.views

urlpatterns = patterns('',
   url(r'^$',                                          lambda request: HttpResponseRedirect('/cropper/t/2wk7srh/page_1/')), 
   url(r'^t/(?P<tinyurl>\w+)/page_(?P<page>\d+)/(?P<cropping>.+?/)?$',      
                                                       cropper.views.croppage, name="croppage"), 
   url(r'^png/t/(?P<tinyurl>\w+)/page_(?P<page>\d+)/(?P<cropping>.+?/)?$', 
                                                       cropper.views.cropimg,  name="cropimg"), 
   )
   
   
