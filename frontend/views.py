from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from scraper.models import Scraper
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

def not_implemented_yet(request):
    return render_to_response('frontend/not-implemented-yet.html', {}, context_instance = RequestContext(request))	