from django.conf.urls.defaults import patterns, url
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import cropper.views

urlpatterns = patterns('',
   url(r'^$',                                          
           lambda request: HttpResponseRedirect(reverse('croppage', args=['2wk7srh', 1]))), 
   url(r'^t/(?P<tinyurl>\w+)/$',                       
           lambda request, tinyurl: HttpResponseRedirect(reverse('croppage', args=[tinyurl, 1]))), 
   url(r'^t/(?P<tinyurl>\w+)/page_(?P<page>\d+)/(?P<cropping>.+?/)?$',      
                                                       cropper.views.croppage, name="croppage"), 
   url(r'^(?P<format>png|pngprev)/t/(?P<tinyurl>\w+)/page_(?P<page>\d+)/(?P<cropping>.+?/)?$', 
                                                       cropper.views.cropimg,  name="cropimg"), 
   )
   
   
