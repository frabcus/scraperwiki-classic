from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib import auth
import settings
from frontend.forms import SigninForm, UserProfileForm

from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from scraper.models import Scraper
from market.models import Solicitation
from frontend.forms import CreateAccountForm
from frontend.models import UserToUserRole
from registration.backends import get_backend
from profiles import views as profile_views

import django.contrib.auth.views
import os
import re
import datetime

def frontpage(request, public_profile_field=None):
    user = request.user

    # The following items are only used when there is a logged in user.	
    if user.is_authenticated():
        my_scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False)
        following_scrapers = user.scraper_set.filter(userscraperrole__role='follow')
        #following_users = UserToUserRole.objects.filter(from_user=user, role='follow')
        following_users = user.to_user.following()
        following_users_count = len(following_users)
        # needs to be expanded to include scrapers you have edit rights on.
        contribution_scrapers = my_scrapers
    else:
        my_scrapers = []
        following_scrapers = []
        following_users = []
        following_users_count = 0
        contribution_scrapers = []
        profile_obj = None

    contribution_count = len(contribution_scrapers)
    good_contribution_scrapers = []
    # add filtering to cut this down to the most recent 10 items
    # also need to add filtering to limit to public published scrapers
    for scraper in contribution_scrapers:
        if scraper.is_good():
            good_contribution_scrapers.append(scraper)

    #new scrapers
    new_scrapers = Scraper.objects.filter(deleted=False, published=True).order_by('-first_published_at')[:5]
    
    #suggested scrapers
    solicitations = Solicitation.objects.filter(deleted=False).order_by('-created_at')[:5]
    
    return render_to_response('frontend/frontpage.html', {'my_scrapers': my_scrapers, 'solicitations': solicitations, 'following_scrapers': following_scrapers, 'following_users': following_users, 'following_users_count' : following_users_count, 'new_scrapers': new_scrapers, 'contribution_count': contribution_count}, context_instance = RequestContext(request))


# Override default profile view to include 'follow' button
def profile_detail(request, username):
		user = request.user
		try:
			profiled_user = User.objects.get(username=username)
		except User.DoesNotExist:
			return HttpResponseRedirect("/404")
		if request.method == 'POST': # if follow form has been submitted
			if user.is_authenticated():
				if (profiled_user in user.to_user.following()):
					u = UserToUserRole.objects.filter(to_user=profiled_user, from_user=user, role='follow')
					u.delete()
					return profile_views.profile_detail(request, username=username, extra_context={ 'following': False, }, )
				else:
					u = UserToUserRole(to_user=profiled_user, from_user=user, role='follow')
					u.save()
					return profile_views.profile_detail(request, username=username, extra_context={ 'following': True, }, )
		else:
			following = UserToUserRole.objects.filter(to_user=profiled_user, from_user=user, role='follow')
			return profile_views.profile_detail(request, username=username, extra_context={ 'following': following, }, )



def process_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('frontpage'))

def login(request):

    error_messages = []

    #grab the redirect URL if set
    redirect = request.GET.get('next', False)
    if request.POST.get('redirect', False):
        redirect = request.POST.get('redirect', False)
    
    
    #Create login and registration forms
    login_form = SigninForm()
    registration_form = CreateAccountForm()

    if request.method == 'POST':

        #Existing user is logging in
        if request.POST.has_key('login'):

            login_form = SigninForm(data=request.POST)
            user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])

            if user is not None:
                if user.is_active:

                    #Log in
                    auth.login(request, user)

                    #set session timeout
                    if request.POST.has_key('remember_me'):
                        request.session.set_expiry(settings.SESSION_TIMEOUT)


                    if redirect:
                        return HttpResponseRedirect(redirect)
                    else:
                        return HttpResponseRedirect(reverse('frontpage'))

                else:
                    # Account exists, but not activated                    
                    error_messages.append("This account has not been activated, please check your email and click on the link to confirm your account")

        #New user is registering
        elif request.POST.has_key('register'):

            registration_form = CreateAccountForm(data=request.POST)

            if registration_form.is_valid():
                backend = get_backend(settings.REGISTRATION_BACKEND)             
                new_user = backend.register(request, **registration_form.cleaned_data)

                #sign straight in
                signed_in_user = auth.authenticate(username=request.POST['username'], password=request.POST['password1'])
                auth.login(request, signed_in_user)                

                #redirect
                if redirect:
                    return HttpResponseRedirect(redirect)
                else:
                    return HttpResponseRedirect(reverse('frontpage'))

    else:
        login_form = SigninForm()
        registration_form = CreateAccountForm()
        message = None

    return render_to_response('registration/extended_login.html', {'registration_form': registration_form, 'login_form': login_form, 'error_messages': error_messages, 'redirect': redirect}, context_instance = RequestContext(request))

        
    