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


    
# unable to make the string 'detectors' be included into the urls function
def scopeindex(request):
    actionmessage = ""
    if request.POST.get("reset"):
        ResetDatabase()
        actionmessage = "The database has been reset"
        
    return render_to_response('scopeindex.html', {'detectors':'detectors', 'readers':'readers', 'collectors':'collectors', 'observers':'observers', 'settings':settings, 'actionmessage':actionmessage})


