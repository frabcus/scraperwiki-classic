from django.conf.urls.defaults import *
import views

#
# producing the variations on the editor/<short_name> URL by appending commands on the end is not ideal
# but works for now and can be changed by altering this file alone
# 

urlpatterns = patterns('',
  url(r'^(?P<short_name>[\-\w]*?)/RUN$',  views.run,        name="editor_run"),         # makes the call to the firebox
  url(r'^(?P<short_name>[\-\w]*?)/SAVE$', views.savecommit, name="editor_savecommit"),  # this requires the code to be POSTed
  url(r'^(?P<short_name>[\-\w]*?)/RAW$',  views.raw,        name="editor_raw"),         # text output of the code along for the reload feature
  url(r'^(?P<short_name>[\-\w]*)$',       views.edit,       name="editor"),             # produces the standard editor page
    
)