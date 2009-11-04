from django.conf.urls.defaults import *
import views
import code_runner

# urls prefixed with "/editor/"

urlpatterns = patterns('',
  
  # COMMENT: a randomly generated scraper name (rather than a blank one), eg "editor/draft-83276436/" would allow for paired coding on a draft, 
  # so I could send the URL to someone else and use simple paired programming techniques over the net.  
  # it would also avoid needing to program the special cases of having a draft in so many places.  
  
  url(r'^$',                            views.edit, name="editor"),    # blank name for draft scraper
  url(r'^(?P<short_name>[\-\w]+)$',     views.edit, name="editor"),
  
  # this doesn't take the short_name as it runs the code in POST.get('code')
  # how will it know what short_name to tag any records it puts into the database with?
  url(r'^run_code$',                    code_runner.run_code, name="run_code"),
  
  url(r'^draft/delete$',                views.delete_draft, name="delete_draft"),
  url(r'^draft/save$',                  views.save_draft,   name="save_draft"),
  
  url(r'diff/$',                        views.diff,         name="diff"),   # blank name for draft scraper
  url(r'diff/(?P<short_name>[\-\w]+)$', views.diff,         name="diff"),
  
  url(r'raw/$',                         views.raw,          name="raw"),   # blank name for draft scraper
  url(r'raw/(?P<short_name>[\-\w]+)$',  views.raw,          name="raw"),   # blank name for draft scraper
  
)