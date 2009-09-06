from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
import settings
import codewiki.models as models
from codewiki.postdata import ResetDatabase
from django.contrib.auth.models import User
import os
import re
import datetime
import runscrapers

    
def frontpage(request):
    actionmessage = ""
    if request.POST.get("reset"):
        ResetDatabase()
        actionmessage = "The database has been reset"
        
    scrapermodules = models.ScraperModule.objects.all()
    params = {'settings':settings, 'actionmessage':actionmessage, "scrapermodules":scrapermodules }
    params["readingsnumber"] = len(models.Reading.objects.all())
    if params["readingsnumber"]:
        params["readingsfirst"] = models.Reading.objects.order_by('scrape_time')[0].scrape_time
        params["readingslast"] = models.Reading.objects.order_by('-scrape_time')[0].scrape_time
    return render_to_response('frontpage.html', params)

