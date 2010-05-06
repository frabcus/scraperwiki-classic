from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
import re

from whitelist import models

def whitelist_user(request):
    url = request.GET.get("url")
    
    whitelist = [ ]
    urlinwhitelist = False
    for whitelistobj in models.Whitelist.objects.filter(urlcolour="white"):
        whitelistobjaccepted = url and re.match(whitelistobj.urlregex, url)
        if whitelistobjaccepted:
            urlinwhitelist = True
        whitelist.append((whitelistobj, whitelistobjaccepted))
            
    blacklist = [ ]
    urlinblacklist = False
    blacklistunlisted = 0
    blacklistunlistedrejected = False
    for blacklistobj in models.Whitelist.objects.filter(urlcolour="black"):
        blacklistobjrejected = url and re.match(blacklistobj.urlregex, url)
        if blacklistobjrejected:
            urlinblacklist = True
        if blacklistobj.urlregexname:
            blacklist.append((blacklistobj, urlinwhitelist and blacklistobjrejected))
        else:
            blacklistunlisted += 1
            if urlinwhitelist and blacklistobjrejected:
                blacklistunlistedrejected = True
    
    data = {'whitelist':whitelist, 'blacklist':blacklist, 
            'blacklistunlisted':blacklistunlisted, 'blacklistunlistedrejected':blacklistunlistedrejected, 
            'url':url, 'urlinwhitelist':urlinwhitelist, 'urlinblacklist':urlinblacklist }
    return render_to_response('whitelist/index.html', data, context_instance=RequestContext(request))

def whitelist_config(request):
    whitelist = models.Whitelist.objects.filter(urlcolour="white")
    white_string = "\n".join([ "white=%s" % obj.urlregex  for obj in whitelist])
    blacklist = models.Whitelist.objects.filter(urlcolour="black")
    black_string = "\n".join([ "black=%s" % obj.urlregex  for obj in blacklist])
    return HttpResponse(white_string + '\n' +black_string)
