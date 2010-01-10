from django.conf.urls.defaults import *
from profiles import views as profile_views
from contact_form.views import contact_form
import frontend.views as frontend_views
import frontend.forms as frontend_forms
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    # profiles
    url(r'^(?P<username>\w+)/$', frontend_views.profile_detail, name='profiles_profile_detail'),
    url(r'^create/$',                     profile_views.create_profile, {'form_class': frontend_forms.UserProfileForm}, name='profiles_create_profile'),
    url(r'^edit/$',                       profile_views.edit_profile, {'form_class': frontend_forms.UserProfileForm},   name='profiles_edit_profile'),
    url(r'^profiles/$',                   profile_views.profile_list, name='profiles_profile_list'),
    # May want to reinstate these next two to give people a link to follow or unfollow a user
    #url(r'^profiles/(?P<username>\w+)/follow/$', profile_views.profile_follow, name='profiles_profile_follow'),
    #url(r'^profiles/(?P<username>\w+)/unfollow/$', profile_views.profile_unfollow, name='profiles_profile_unfollow'),

    url(r'^login/$',                      frontend_views.login, name='login'),
    url(r'^login/confirm/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/confirm_account.html'}, name='confirm_account'),          
    url(r'^help/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/help.html'}, name='help'),   
    url(r'^terms_and_conditions/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/terms_and_conditions.html'}, name='terms'),   
    url(r'^privacy/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/privacy.html'}, name='privacy'),       
    url(r'^about/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/about.html'}, name='about'),       
    url(r'^example_data/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/example_data.html'}, name='api'),       


    # contact form
    url(r'^contact/$',                    contact_form, {'form_class':frontend_forms.scraperContactForm},name='contact_form'),
    url(r'^contact/sent/$',               direct_to_template,{ 'template': 'contact_form/contact_form_sent.html' },name='contact_form_sent'),
    
    # user's scrapers
    url(r'^my-scrapers/$',                  frontend_views.my_scrapers, name='my_scrapers'),
    
    # Example pages to scrape :)
    url(r'^examples/basic_table\.html$',  direct_to_template,{ 'template': 'examples/basic_table.html' },name='example_basic_table'),
   )






