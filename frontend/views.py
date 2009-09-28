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
  return render_to_response('frontend/frontpage.html', {}, context_instance = RequestContext(request))

def process_logout(request):
  logout(request)
  return HttpResponseRedirect(reverse('frontpage'))
	