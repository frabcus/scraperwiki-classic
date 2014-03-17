from django.conf.urls.defaults import *

# a not very well namespaced django plugin class
from profiles import views as profile_views
from contact_form.views import contact_form
import frontend.views as frontend_views
import frontend.forms as frontend_forms

from django.views.generic.simple import redirect_to, direct_to_template
from frontend.models import Feature

urlpatterns = patterns('',

    # profiles
    url(r'^profiles/edit/$', profile_views.edit_profile, {'form_class': frontend_forms.UserProfileForm}, name='profiles_edit_profile'),
    url(r'^profiles/(?P<username>.*)/message/$', frontend_views.user_message, name='user_message'),
    url(r'^profiles/(?P<username>.*)/$', frontend_views.profile_detail, name='profile'),
    url(r'^dashboard/$',
      frontend_views.redirect_dashboard_to_profile,
      name='dashboard'),
    # This duplicate is provided because the standard profiles
    # plugin requires that 'profiles_profile_detail' work when
    # using reverse().
    url(r'^profiles/(?P<username>.*)/$', frontend_views.profile_detail, name='profiles_profile_detail'),
    #url(r'^profiles/', include('profiles.urls')),

    url(r'^terms_and_conditions/$', direct_to_template, {'template': 'frontend/terms_and_conditions.html'}, name='terms'),
    url(r'^privacy/$', direct_to_template, {'template': 'frontend/privacy.html'}, name='privacy'),
    url(r'^jobs/$', direct_to_template, {'template': 'frontend/jobs.html'}, name='jobs'),
    url(r'^tour/$', redirect_to, {'url': '/about/'}, name='tour'),
    url(r'^example_data/$', direct_to_template, {'template': 'frontend/example_data.html'}, name='api'),
    url(r'^help/(?P<mode>intro|faq|tutorials|documentation|code_documentation|libraries)/(?P<language>python|php|ruby|javascript)/$','django.views.generic.simple.redirect_to', {'url': '/docs/%(language)s'},name='help'),
    url(r'^help/(?P<mode>intro|faq|tutorials|documentation|code_documentation|libraries)/$','django.views.generic.simple.redirect_to', {'url': '/docs/'}, name='help_default'),
    url(r'^help/$','django.views.generic.simple.redirect_to', {'url': '/docs/'}, name='help_default'),

    #hello world
    url(r'^hello_world.html', direct_to_template, {'template': 'frontend/hello_world.html'}, name='help_hello_world'),

    # user's scrapers
    url(r'^vaults/(?P<vaultid>\d+)/transfer/(?P<username>.*)/$', frontend_views.transfer_vault, name='transfer_vault'),
    url(r'^vaults/(?P<vaultid>\d+)/(?P<action>adduser|removeuser)/(?P<username>.*)/$', frontend_views.vault_users, name='vault_user'),
    url(r'^vaults/(?P<vaultid>\d+)/addscraper/(?P<shortname>.*)/$', frontend_views.vault_scrapers_add, name='vault_scrapers_add'),
    url(r'^vaults/(?P<vaultid>\d+)/removescraper/(?P<shortname>.*)/(?P<newstatus>public|visible)$', frontend_views.vault_scrapers_remove, name='vault_scrapers_remove'),
    url(r'^vaults/$', frontend_views.view_vault, name='vault'),
    url(r'^vaults/new/$', frontend_views.new_vault, name='new_vault'),

    # Example pages to scrape :)
    url(r'^examples/basic_table\.html$', direct_to_template, {'template': 'examples/basic_table.html'}, name='example_basic_table'),
    # for testing error handling
    url(r'^test_error/$',                  frontend_views.test_error, name='test_error'),

    #searching and browsing
    url(r'^search/$', frontend_views.search, name='search'),
    url(r'^search/(?P<q>.+)/$', frontend_views.search, name='search'),

    url(r'^browse/(?P<page_number>\d+)?$', frontend_views.browse, name='scraper_list'),
    url(r'^browse/(?P<wiki_type>scraper|view)s/(?P<page_number>\d+)?$', frontend_views.browse_wiki_type, name='scraper_list_wiki_type'),
    url(r'^tags/$', frontend_views.tags, name='all_tags'),
    url(r'^tags/(?P<tag>[^/]+)$', frontend_views.tag, name='single_tag'),

    #events
    url(r'^events/(?P<e>[^/]+)?/?$', frontend_views.events, name='events'),
)
