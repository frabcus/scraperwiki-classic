from django import forms
from django.http import HttpResponseRedirect
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
        
    params = {'settings':settings, 'actionmessage':actionmessage}
    modulelist = ['detectors', 'readers', 'collectors', 'observers']
    for key in modulelist:
        params[key] = key   # don't know how to enter in absolute strings in the {% url %} function
        params[key + "scripts"] = models.ScraperScript.objects.filter(dirname=key)[:3]
    params["readingsnumber"] = len(models.Reading.objects.all())
    if params["readingsnumber"]:
        params["readingsfirst"] = models.Reading.objects.order_by('scrape_time')[0].scrape_time
        params["readingslast"] = models.Reading.objects.order_by('-scrape_time')[0].scrape_time
    return render_to_response('frontpage.html', params)


def observer(request, observername, tail):
    exename = os.path.join(settings.MODULES_DIR, "observers", observername + ".py")
    ptail = tail and (" --tail " + tail) or ""
    pqs = request.META["QUERY_STRING"] and (" --query " + request.META["QUERY_STRING"]) or ""
    sparam = "render" + ptail + pqs
    content = runscrapers.RunFileA(exename, sparam) 
    return HttpResponse(content=content)


