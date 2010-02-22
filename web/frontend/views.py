from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
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

    hide_logo = False
    grey_body = False    
    template = 'frontend/frontpage.html'
    # The following items are only used when there is a logged in user.	
    if user.is_authenticated():
        my_scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False).order_by('-created_at')
        following_scrapers = user.scraper_set.filter(userscraperrole__role='follow', deleted=False).order_by('-created_at')
        following_users = user.to_user.following()
        following_users_count = len(following_users)
        # contribution_scrapers needs to be expanded to include scrapers you have edit rights on
        contribution_scrapers = my_scrapers
        template = 'frontend/frontpage_logged_in.html'        
    else:
        hide_logo = True
        grey_body = True
        my_scrapers = []
        following_scrapers = []
        following_users = []
        following_users_count = 0
        contribution_scrapers = []
        profile_obj = None

    contribution_count = len(contribution_scrapers)
    good_contribution_scrapers = []
    # cut number of scrapers displayed on homepage down to the most recent 10 items
    my_scrapers = my_scrapers[:10]
    has_scrapers = len(my_scrapers) > 0
    # also need to add filtering to limit to public published scrapers
    for scraper in contribution_scrapers:
        if scraper.is_good():
            good_contribution_scrapers.append(scraper)

    #new scrapers
    new_scrapers = Scraper.objects.filter(deleted=False, published=True, featured=False).order_by('-first_published_at')[:5]
    featured_scrapers = Scraper.objects.filter(deleted=False, published=True, featured=True).order_by('-first_published_at')[:5]    
    
    #suggested scrapers
    solicitations = Solicitation.objects.filter(deleted=False).order_by('-created_at')[:5]
    
    return render_to_response(template, {'grey_body': grey_body, 'hide_logo': hide_logo, 'my_scrapers': my_scrapers, 'has_scrapers':has_scrapers, 'solicitations': solicitations, 'following_scrapers': following_scrapers, 'following_users': following_users, 'following_users_count' : following_users_count, 'new_scrapers': new_scrapers, 'featured_scrapers': featured_scrapers, 'contribution_count': contribution_count}, context_instance = RequestContext(request))


def my_scrapers(request):
	user = request.user

	if user.is_authenticated():
	    
	    #scrapers
		owned_scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False)
		owned_count = len(owned_scrapers) 
		
		# needs to be expanded to include scrapers you have edit rights on.
		contribution_scrapers = user.scraper_set.filter(userscraperrole__role='editor', deleted=False)
		contribution_count = len(contribution_scrapers)
		following_scrapers = user.scraper_set.filter(userscraperrole__role='follow', deleted=False)
		following_count = len(following_scrapers)
	else:
		return HttpResponseRedirect(reverse('frontpage'))

	return render_to_response('frontend/my_scrapers.html', {'owned_scrapers': owned_scrapers, 'owned_count' : owned_count, 'contribution_scrapers' : contribution_scrapers, 'contribution_count': contribution_count, 'following_scrapers' : following_scrapers, 'following_count' : following_count, }, context_instance = RequestContext(request))


# Override default profile view to include 'follow' button
def profile_detail(request, username):
		user = request.user
		try:
			profiled_user = User.objects.get(username=username)
		except User.DoesNotExist:
			raise Http404

        owned_scrapers = profiled_user.scraper_set.filter(userscraperrole__role='owner', published=True, deleted=False)
		solicitations = market.models.Solicitation.objects.filter(deleted=False, status=status).order_by('-created_at')[:5]        
		
		if request.method == 'POST': # if follow form has been submitted
			if user.is_authenticated():
				if (profiled_user in user.to_user.following()):
					u = UserToUserRole.objects.filter(to_user=profiled_user, from_user=user, role='follow')
					u.delete()
					return profile_views.profile_detail(request, username=username, extra_context={ 'following': False, 'owned_scrapers' : owned_scrapers, }, )
				else:
					u = UserToUserRole(to_user=profiled_user, from_user=user, role='follow')
					u.save()
					return profile_views.profile_detail(request, username=username, extra_context={ 'following': True, 'owned_scrapers' : owned_scrapers, }, )
		else:
			following = UserToUserRole.objects.filter(to_user=profiled_user, from_user=user, role='follow')
			return profile_views.profile_detail(request, username=username, extra_context={ 'following' : following, 'owned_scrapers' : owned_scrapers, } )


def edit_profile(request):
                form = UserProfileForm()
                return profile_views.edit_profile(request, form_class=form)

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
            user = auth.authenticate(username=request.POST['user_or_email'], password=request.POST['password'])

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

            else:
                # Account not found                  
                error_messages.append("Sorry, but we could not find that username or email address")


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

        
    