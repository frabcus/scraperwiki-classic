from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse

from whitelist import models

def whitelist_user (request):
    whitelist = models.Whitelist.objects.filter(urlcolour="white")
    blacklist = models.Whitelist.objects.filter(urlcolour="black")
    return render_to_response('whitelist/index.html', {'whitelist' : whitelist, 'blacklist': blacklist }, context_instance = RequestContext(request))

def whitelist_white(request):
    whitelist = models.Whitelist.objects.filter(urlcolour="white")
    return HttpResponse("\n".join([ obj.urlregex  for obj in whitelist]))

def whitelist_black(request):
    whitelist = models.Whitelist.objects.filter(urlcolour="black")
    return HttpResponse("\n".join([ obj.urlregex  for obj in whitelist]))
            