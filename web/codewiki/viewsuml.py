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

from codewiki.management.commands.run_scrapers import GetUMLrunningstatus, killrunevent


def run_event(request, event_id):
    user = request.user
    event = get_object_or_404(ScraperRunEvent, id=event_id)
    outputlines = event.output.split("\n")
    
    context = { 'outputlines':outputlines, 'event':event }
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['runID'] == event.run_id:
            context['status'] = status
    
    context['scraper'] = event.scraper
    context['selected_tab'] = ''
    context['user_owns_it'] = (event.scraper.owner() == user)
    
    return render_to_response('codewiki/run_event.html', context, context_instance=RequestContext(request))


def running_scrapers(request):
    #events = ScraperRunEvent.objects.filter(run_ended=None)
    recentevents = ScraperRunEvent.objects.all().order_by('-run_started')[:10]

    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['scraperID']:
            status['scraper'] = Code.objects.get(guid=status['scraperID'])   # could throw ObjectDoesNotExist
        
        scraperrunevents = ScraperRunEvent.objects.filter(run_id=status['runID'])
        if scraperrunevents:
            status['scraperrunevent'] = scraperrunevents[0]
    
    context = { 'statusscrapers': statusscrapers, 'events':recentevents }
    return render_to_response('codewiki/running_scrapers.html', context, context_instance=RequestContext(request))


def scraper_killrunning(request, run_id):
    event = get_object_or_404(ScraperRunEvent, run_id=run_id)
    if event.scraper.owner() != request.user and not request.user.is_staff:
        raise Http404
    if request.POST.get('killrun', None) == '1':
        success = killrunevent(event)
    time.sleep(1)
    return HttpResponseRedirect(reverse('run_event', args=[event.id]))

