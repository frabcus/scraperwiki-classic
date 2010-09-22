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

from codewiki.management.commands.run_scrapers import GetUMLrunningstatus

def run_event(request, event_id):
    user = request.user
    event = get_object_or_404(ScraperRunEvent, id=event_id)
    
    context = { 'event':event }
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['runID'] == event.run_id:
            context['status'] = status
    
    context['scraper'] = event.scraper
    context['selected_tab'] = ''
    context['user_owns_it'] = (event.scraper.owner() == user)
    
    return render_to_response('codewiki/run_event.html', context, context_instance=RequestContext(request))


def running_scrapers(request):
    # uncomment next line when run_started is indexed
    #recentevents = ScraperRunEvent.objects.all().order_by('-run_started')[:10]  
    recentevents = ScraperRunEvent.objects.all().order_by('-id')[:10]
    recentid = recentevents and recentevents[0].id or 100
    
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['scraperID']:
            status['scraper'] = Code.objects.get(guid=status['scraperID'])   # could throw ObjectDoesNotExist
        
        # filtering necessary because run_id is not indexed
        scraperrunevents = ScraperRunEvent.objects.filter(id__gt=recentid-100).filter(run_id=status['runID'])
        if scraperrunevents:
            status['scraperrunevent'] = scraperrunevents[0]
    
    context = { 'statusscrapers': statusscrapers, 'events':recentevents }
    return render_to_response('codewiki/running_scrapers.html', context, context_instance=RequestContext(request))


# doesn't work for scrapers that are run by the cronjob (only those that are run from a browser)
# alternative method is to invoke a kill operation in the dispatcher, (the localhost:9000 link)
def scraper_killrunning(request, run_id):
    recentevents = ScraperRunEvent.objects.all().order_by('-id')[:1]
    recentid = recentevents and recentevents[0].id or 100
    
    # filtering necessary because run_id is not indexed
    #event = get_object_or_404(ScraperRunEvent, run_id=run_id)
    event = ScraperRunEvent.objects.filter(id__gt=recentid-100).filter(run_id=run_id)[0]
    
    if event.scraper.owner() != request.user and not request.user.is_staff:
        raise Http404
    
    pid = event.pid
    if request.POST.get('killrun', None) == '1' and pid != -1:
        try:
            os.kill(pid, signal.SIGKILL)
            success = True
        except OSError, e:
            if e.errno != 3:   # No such process
                return HttpResponse("Kill failed: " + str(e) + " " + str(e.errno))
    
    time.sleep(1)
    return HttpResponseRedirect(reverse('run_event', args=[event.id]))

