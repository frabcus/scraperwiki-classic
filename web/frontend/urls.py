from django.conf.urls.defaults import *


from profiles import views as profile_views  # a not very well namespaced django plugin class
from contact_form.views import contact_form
import frontend.views as frontend_views  # who thinks replacing dots with underscores here is useful?? --JT
import frontend.forms as frontend_forms

from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    # profiles
    url(r'^profiles/edit/$', profile_views.edit_profile, {'form_class': frontend_forms.UserProfileForm, 
                                                          'extra_context': {'body_class': 'profile'}}, name='profiles_edit_profile'),
    url(r'^profiles/(?P<username>\w+)/$', frontend_views.profile_detail, name='profiles_profile_detail'),
    #url(r'^profiles/', include('profiles.urls')), 

    url(r'^login/$',frontend_views.login, name='login'),
    url(r'^login/confirm/$', direct_to_template, {'template': 'registration/confirm_account.html',
                                                  'extra_context': {'body_class': 'confirm_account'}}, name='confirm_account'),
    url(r'^terms_and_conditions/$', direct_to_template, {'template': 'frontend/terms_and_conditions.html',
                                                         'extra_context': {'body_class': 'terms'}}, name='terms'),
    url(r'^privacy/$', direct_to_template, {'template': 'frontend/privacy.html',
                                            'extra_context': {'body_class': 'privacy'}}, name='privacy'),
    url(r'^about/$', direct_to_template, {'template': 'frontend/about.html',
                                          'extra_context': {'body_class': 'about'}}, name='about'),
    url(r'^tour/$', direct_to_template, {'template': 'frontend/tour.html',
                                          'extra_context': {'body_class': 'tour'}}, name='tour'),                                          
    url(r'^example_data/$', direct_to_template, {'template': 'frontend/example_data.html',
                                                 'extra_context': {'body_class': 'example_data'}}, name='api'),
    url(r'^help/$',frontend_views.help, name='help'),

    url(r'^help/(?P<mode>faq|tutorials|documentation|code_documentation|libraries)/$',frontend_views.help, name='help_default'),
    url(r'^help/(?P<mode>faq|tutorials|documentation|code_documentation|libraries)/(?P<language>python|php|ruby)/$',frontend_views.help, name='help'),
    url(r'^get_involved/$',frontend_views.get_involved, name='get_involved'),
    
    #hello world
    url(r'^hello_world.html', direct_to_template, {'template': 'frontend/hello_world.html'}, name='help_hello_world'),

    # contact form
    url(r'^contact/$', contact_form, {'form_class': frontend_forms.scraperContactForm, 'extra_context': {'body_class': 'contact'}}, name='contact_form'),
    url(r'^contact/sent/$', direct_to_template, {'template': 'contact_form/contact_form_sent.html',
                                                 'extra_context': {'body_class': 'contact_form_sent'}}, name='contact_form_sent'),
    
    # user's scrapers
    url(r'^dashboard/$',                  frontend_views.dashboard, name='dashboard'),
    url(r'^stats/$',                  frontend_views.stats, name='stats'),    
    
    # Example pages to scrape :)
    url(r'^examples/basic_table\.html$', direct_to_template, {'template': 'examples/basic_table.html'}, name='example_basic_table'),
    
    #searching and browsing
    url(r'^search/$', frontend_views.search, name='search'),
    url(r'^search/(?P<q>.+)/$', frontend_views.search, name='search'),

    url(r'^browse/(?P<page_number>\d+)?$', frontend_views.browse, name='scraper_list'),    
    url(r'^browse/(?P<wiki_type>scraper|view)s/(?P<page_number>\d+)?$', frontend_views.browse_wiki_type, name='scraper_list_wiki_type'),
    url(r'^tags/$', frontend_views.tags, name='all_tags'),    
    url(r'^tags/(?P<tag>[^/]+)$', frontend_views.tag, name='single_tag'),                       
   )






