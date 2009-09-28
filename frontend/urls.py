from django.conf.urls.defaults import *
from profiles import views
import frontend.forms as frontend_forms

urlpatterns = patterns('',
   url(r'^create/$', views.create_profile, {'form_class': frontend_forms.UserProfileForm}, name='profiles_create_profile'),
   url(r'^profiles/edit/$', views.edit_profile, {'form_class': frontend_forms.UserProfileForm}, name='profiles_edit_profile'),
   url(r'^profiles/(?P<username>\w+)/$', views.profile_detail, name='profiles_profile_detail'),
   url(r'^profiles/$', views.profile_list, name='profiles_profile_list'),
   )
