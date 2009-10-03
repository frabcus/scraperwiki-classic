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

def show(request, scraper_id = 0, selected_tab = 'data'):
    user = request.user
    scraper = models.Scraper.objects.get(id=scraper_id)
    you_own_it = (scraper.owner() == user)
    you_follow_it = (user in scraper.followers())
    tabs = [
	  {'code': 'data', 'title': 'Data',       'template': 'scraper/data_tab.html'},
	  {'code': 'code', 'title': 'Code',       'template': 'scraper/code_tab.html'},
	  {'code': 'hist', 'title': 'History',    'template': 'scraper/hist_tab.html'},
	  {'code': 'disc', 'title': 'Discussion', 'template': 'scraper/disc_tab.html'},
	  {'code': 'edit', 'title': 'Editors',    'template': 'scraper/edit_tab.html'}
    ]
	
    # include a default value, just in case someone frigs the URL
    tab_to_show = 'scraper/data_tab.html'
    for tab in tabs:
        if tab['code'] == selected_tab:
            tab['class'] = 'selected tab'
            tab['selected'] = True
            tab_to_show = tab['template']
        else:
            tab['class'] = 'tab'
            tab['selected'] = False
			
    return render_to_response('scraper/show.html', {'selected_tab': selected_tab, 'scraper': scraper, 'you_own_it': you_own_it, 'you_follow_it': you_follow_it, 'tabs': tabs, 'tab_to_show': tab_to_show}, context_instance=RequestContext(request))