from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib import auth
import settings
from django.contrib.auth.forms import AuthenticationForm

from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from scraper.models import Scraper
from registration.forms import RegistrationForm
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

    new_scrapers = Scraper.objects.all()
    return render_to_response('frontend/frontpage.html', {'my_scrapers': my_scrapers, 'following_scrapers': following_scrapers, 'new_scrapers': new_scrapers, 'contribution_count': contribution_count}, context_instance = RequestContext(request))

def process_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('frontpage'))
    
def login(request):
    if request.method == 'POST':
        login_form = AuthenticationForm(data=request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('frontpage'))
                
                # Redirect to a success page.
            else:
                message = "This account has not been activated, please check your email for confirmation"
                # Return a 'disabled account' error message
        else:
            message = "Invalid Login"
            # Return an 'invalid login' error message.
    else:
        login_form = AuthenticationForm()
        registration_form = RegistrationForm()
        message = None
        
    return render_to_response('registration/extended_login.html', {'login_form': login_form, 'registration_form': registration_form, 'message': message}, context_instance = RequestContext(request))
    