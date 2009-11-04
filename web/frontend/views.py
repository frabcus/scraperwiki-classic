from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib import auth
import settings
from frontend.forms import SigninForm

from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from scraper.models import Scraper
from frontend.forms import CreateAccountForm
from registration.backends import get_backend

import django.contrib.auth.views
import os
import re
import datetime

def frontpage(request):
    user = request.user
	
    # The following items are only used when there is a logged in user.	
    if user.is_authenticated():
        my_scrapers = user.scraper_set.filter(userscraperrole__role='owner')
        following_scrapers = user.scraper_set.filter(userscraperrole__role='follow')

        # needs to be expanded to include scrapers you have edit rights on.
        contribution_scrapers = my_scrapers
    else:
        my_scrapers = []
        following_scrapers = []
        contribution_scrapers = []

    contribution_count = len(contribution_scrapers)
    good_contribution_scrapers = []
    # add filtering to cut this down to the most recent 10 items
    # also need to add filtering to limit to public published scrapers
    for scraper in contribution_scrapers:
        if scraper.is_good():
            good_contribution_scrapers.append(scraper)

    new_scrapers = Scraper.objects.all().order_by('-created_at')[:5]
    return render_to_response('frontend/frontpage.html', {'my_scrapers': my_scrapers, 'following_scrapers': following_scrapers, 'new_scrapers': new_scrapers, 'contribution_count': contribution_count}, context_instance = RequestContext(request))

def process_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('frontpage'))

def login(request):

    error_messages = []

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

                    #Check if scrapers pending in session - added here as contrib.auth doesn't support signals :(
                    if request.session.get('ScraperDraft', False):
                      return HttpResponseRedirect(
                        reverse('editor') + "?action=%s" % request.session['ScraperDraft'].action
                        )

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
                return HttpResponseRedirect(reverse('confirm_account'))
    else:
        login_form = SigninForm()
        registration_form = CreateAccountForm()
        message = None

    return render_to_response('registration/extended_login.html', {'registration_form': registration_form, 'login_form': login_form, 'error_messages': error_messages}, context_instance = RequestContext(request))

        
    