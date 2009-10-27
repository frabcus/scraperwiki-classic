from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
  url(r'^(?P<short_name>[\-\w]*?)/RUN$',  views.run,        name="editor_run"),         # will call to the firebox
  url(r'^(?P<short_name>[\-\w]*?)/SAVE$', views.savecommit, name="editor_savecommit"),  # this requires the code to be POSTed
  url(r'^(?P<short_name>[\-\w]*)$',       views.edit,       name="editor"),
    
)