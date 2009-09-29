from django.template import RequestContext
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from scraper import models

def create(request):
    if request.method == 'POST':
        return render_to_response('scraper/create.html', {}, context_instance=RequestContext(request)) 
    else:
        return render_to_response('scraper/create.html', {}, context_instance=RequestContext(request)) 