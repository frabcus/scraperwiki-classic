from django.conf.urls.defaults import *
import views
import code_runner

# urls prefixed with "/editor/"

urlpatterns = patterns('',
  #TODO: limit draft action to commit/save
  # The order of these is very important to
  url(r'^run_code$',                    code_runner.run_code, name="run_code"),
  url(r'^handle_session_draft/(?P<action>[\-\w]+)$',     views.handle_session_draft, name="handle_session_draft"),
  url(r'^$',                            views.edit, name="editor"),    # blank name for draft scraper
  url(r'^(?P<short_name>[\-\w]+)$',     views.edit, name="editor"),
  
  
  url(r'^draft/delete/$',                views.delete_draft, name="delete_draft"),
  
  url(r'diff/$',                        views.diff,         name="diff"),   # blank name for draft scraper
  url(r'diff/(?P<short_name>[\-\w]+)$', views.diff,         name="diff"),
  
  url(r'raw/$',                         views.raw,          name="raw"),   # blank name for draft scraper
  url(r'raw/(?P<short_name>[\-\w]+)$',  views.raw,          name="raw"),   # blank name for draft scraper
  
)