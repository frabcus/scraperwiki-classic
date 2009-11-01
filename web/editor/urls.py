from django.conf.urls.defaults import *
import views
import code_runner

urlpatterns = patterns('',
  url(r'^draft/delete$', views.delete_draft, name="delete_draft"),
  url(r'^draft/save$', views.save_draft, name="save_draft"),
  url(r'diff/(?P<short_name>[\-\w]+)', views.diff, name="diff"),
  url(r'^$', views.edit, name="editor"),
  url(r'^run_code$', code_runner.run_code, name="run_code"),
  url(r'^(?P<short_name>[\-\w]+)$', views.edit, name="editor"),
  
)