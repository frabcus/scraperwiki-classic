from django.conf.urls.defaults import *
import views
import code_runner

urlpatterns = patterns('',
  url(r'^draft/delete$', views.delete_draft, name="delete_draft"),
  url(r'^draft/save$', views.save_draft, name="save_draft"),
  url(r'diff/(?P<short_name>[\-\w]+)', views.diff, name="diff"),
  url(r'^$', views.edit, name="editor"),    # blank name for draft scraper
  url(r'diff/', views.diff, name="diff"),   # blank name for draft scraper
  url(r'^run_code$', code_runner.run_code, name="run_code"),
  url(r'^(?P<short_name>[\-\w]+)$', views.edit, name="editor"),
  
  # comment: a randomly generated scraper name (rather than a blank one), eg "editor/draft-83276436/" would allow for paired coding on a draft, 
  # so I could send the URL to someone else and use simple paired programming techniques over the net.  
  # it would also avoid needing to run the special case of a draft so deeply.  
)