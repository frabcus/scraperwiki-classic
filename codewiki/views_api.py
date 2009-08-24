from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
import settings
import codewiki.models as models
import os
import re
import datetime
import runscrapers

def observer(request, observername, tail):
    exename = os.path.join(settings.MODULES_DIR, "observers", observername + ".py")
    ptail = tail and (" --tail " + tail) or ""
    pqs = request.META["QUERY_STRING"] and (" --query " + request.META["QUERY_STRING"]) or ""
    sparam = "render" + ptail + pqs
    content = runscrapers.RunFileA(exename, sparam) 
    return HttpResponse(content=content)

