from django.conf.urls.defaults import *
import views
import code_runner

# urls prefixed with "/editor/"

urlpatterns = patterns('',

  # DO NOT MOVE THIS LINE BELOW ANY OTHER LINE UNLESS YOU KNOW WHAT YOU ARE DOING
  url(r'^run_code$',                    code_runner.run_code, name="run_code"),
  
  url(r'^$',                            views.edit, name="editor"),    # blank name for draft scraper
  url(r'^(?P<short_name>[\-\w]+)$',     views.edit, name="editor"),
  
  
  url(r'^draft/delete/(?P<short_name>[\-\w]+)$',                views.delete_draft, name="delete_draft"),
  url(r'^draft/save/(?P<short_name>[\-\w]+)$',                  views.save_draft,   name="save_draft"),
  
  url(r'diff/$',                        views.diff,         name="diff"),   # blank name for draft scraper
  url(r'diff/(?P<short_name>[\-\w]+)$', views.diff,         name="diff"),
  
  url(r'raw/$',                         views.raw,          name="raw"),   # blank name for draft scraper
  url(r'raw/(?P<short_name>[\-\w]+)$',  views.raw,          name="raw"),   # blank name for draft scraper
  
)