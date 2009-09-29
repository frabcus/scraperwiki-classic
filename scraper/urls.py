from django.conf.urls.defaults import *

from scraper import views


urlpatterns = patterns('',
                       url(r'^create/$',
                           views.create,
                           name='scraper_create'),
                       )

