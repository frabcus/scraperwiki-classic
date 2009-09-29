from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.template import RequestContext
from django.core.urlresolvers import reverse

import os
import re
import datetime

def frontpage(request):
    my_scrapers = request.user.scraper_set.filter(userscraperrole__role='owner')
    following_scrapers = request.user.scraper_set.filter(userscraperrole__role='follow')
    return render_to_response('frontend/frontpage.html', {'my_scrapers': my_scrapers, 'following_scrapers': following_scrapers}, context_instance = RequestContext(request))

def process_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('frontpage'))

def not_implemented_yet(request):
    return render_to_response('frontend/not-implemented-yet.html', {}, context_instance = RequestContext(request))	