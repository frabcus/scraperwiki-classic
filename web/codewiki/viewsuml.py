from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from codewiki.models import Scraper, Code, ScraperRunEvent

import vc
import frontend

import re
import StringIO, csv, types
import datetime
import time
import os
import signal

from codewiki.management.commands.run_scrapers import GetUMLrunningstatus, kill_running_runid
from viewsrpc import testactiveumls


def run_event(request, event_id):
    user = request.user
    event = get_object_or_404(ScraperRunEvent, id=event_id)
    
    context = { 'event':event }
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['runID'] == event.run_id:
            context['status'] = status
    
    context['scraper'] = event.scraper
    context['selected_tab'] = '' and message.get('message_sub_type') != 'consolestatus'
    context['user_owns_it'] = (event.scraper.owner() == user)
    
    return render_to_response('codewiki/run_event.html', context, context_instance=RequestContext(request))


            

def running_scrapers(request):
    user = request.user
    recentevents = ScraperRunEvent.objects.all().order_by('-run_started')[:10]  
    
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['scraperID']:
            scrapers = Code.objects.filter(guid=status['scraperID'])
            if scrapers:
                status['scraper'] = scrapers[0]
        
        scraperrunevents = ScraperRunEvent.objects.filter(run_id=status['runID'])
        status['killable'] = user.is_staff
        if scraperrunevents:
            status['scraperrunevent'] = scraperrunevents[0]
            if status['scraper'].owner() == user:
                status['killable'] = True

    context = { 'statusscrapers': statusscrapers, 'events':recentevents }
    context['activeumls'] = testactiveumls(5)

    return render_to_response('codewiki/running_scrapers.html', context, context_instance=RequestContext(request))


def scraper_killrunning(request, run_id, event_id):
    user = request.user
    event = event_id and get_object_or_404(ScraperRunEvent, id=event_id) or None
    
    # staff or scraper owner only
    if not (request.user.is_staff or (event and event.scraper.owner() == request.user)):
        raise Http404
    
    if request.POST.get('killrun', None) == '1':
        killed = kill_running_runid(run_id)
        print "Kill function result on", killed
    
    time.sleep(1)
    
    if event:
        return HttpResponseRedirect(reverse('run_event', args=[event.id]))
    return HttpResponseRedirect(reverse('running_scrapers'))

