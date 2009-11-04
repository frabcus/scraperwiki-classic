from django.conf.urls.defaults import *
from profiles import views as profile_views
from contact_form.views import contact_form
import frontend.views as frontend_views
import frontend.forms as frontend_forms
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    # profiles
    url(r'^create/$',                     profile_views.create_profile, {'form_class': frontend_forms.UserProfileForm}, name='profiles_create_profile'),
    url(r'^profiles/edit/$',              profile_views.edit_profile, {'form_class': frontend_forms.UserProfileForm},   name='profiles_edit_profile'),
    url(r'^profiles/(?P<username>\w+)/$', profile_views.profile_detail, name='profiles_profile_detail'),
    url(r'^profiles/$',                   profile_views.profile_list, name='profiles_profile_list'),



    url(r'^login/$',                      frontend_views.login, name='login'),
    url(r'^login/confirm/$', 'django.views.generic.simple.direct_to_template', {'template': 'registration/confirm_account.html'}, name='confirm_account'),          
    url(r'^help/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/help.html'}, name='help'),   
    url(r'^terms_and_conditions/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/terms_and_conditions.html'}, name='terms'),   
    url(r'^about/$', 'django.views.generic.simple.direct_to_template', {'template': 'frontend/about.html'}, name='about'),       

    # contact form
    url(r'^contact/$',                    contact_form, {'form_class':frontend_forms.scraperContactForm},name='contact_form'),
    url(r'^contact/sent/$',               direct_to_template,{ 'template': 'contact_form/contact_form_sent.html' },name='contact_form_sent'),
   )






