from django.conf.urls.defaults import *

from scraper import views


urlpatterns = patterns('',
                       url(r'^create/$',
                           views.create,
                           name='scraper_create'),
                       url(r'^show/(?P<scraper_id>[\w_\-]+)(/(?P<selected_tab>[\w]+))?$',
                           views.show,
                           name='scraper_show'),
                       )

