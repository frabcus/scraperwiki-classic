from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from settings import MAX_API_ITEMS, API_DOMAIN
from scraper.models import Scraper

from django.contrib.auth.decorators import login_required

from models import api_key
from forms import applyForm

import urllib

@login_required
def keys(request):
    
    user = request.user
    users_keys = api_key.objects.filter(user=user)

    key = api_key(user=user)
    form = applyForm()
    
    if request.method == 'POST':
        form = applyForm(data=request.POST, files=request.FILES,instance=key)
        if form.is_valid():
            form.save(commit=False)
            form.save()
            form = applyForm() #clear the form
        #return HttpResponseRedirect(request.path_info)

    return render_to_response('keys.html', {'keys' : users_keys,'form' : form}, context_instance=RequestContext(request))

def explore_scraper_search_1_0(request):
    return render_to_response('scraper_search_1.0.html', {'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_search')}, context_instance=RequestContext(request))

def explore_scraper_getinfo_1_0(request):

    scrapers = []
    user = request.user
    if user.is_authenticated():
        scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False, published=True)[:5]
    else:    
        scrapers = Scraper.objects.filter(deleted=False, published=True).order_by('first_published_at')[:5]

    return render_to_response('scraper_getinfo_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getinfo')}, context_instance=RequestContext(request))

def explore_scraper_getdata_1_0(request):

    scrapers = []
    user = request.user
    if user.is_authenticated():
        scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False, published=True)[:5]
    else:    
        scrapers = Scraper.objects.filter(deleted=False, published=True).order_by('first_published_at')[:5]
    
    return render_to_response('scraper_getdata_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdata')}, context_instance=RequestContext(request))

def explore_scraper_getdatabydate_1_0(request):

    scrapers = []
    user = request.user
    if user.is_authenticated():
        scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False, published=True)[:5]
    else:
        scrapers = Scraper.objects.filter(deleted=False, published=True).order_by('first_published_at')[:5]

    return render_to_response('scraper_getdatabydate_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabydate')}, context_instance=RequestContext(request))    

def explore_scraper_getdatabylocation_1_0(request):

    scrapers = []
    user = request.user
    if user.is_authenticated():
        scrapers = user.scraper_set.filter(userscraperrole__role='owner', deleted=False, published=True)[:5]
    else:    
        scrapers = Scraper.objects.filter(deleted=False, published=True).order_by('first_published_at')[:5]    

    return render_to_response('scraper_getdatabylocation_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabylocation')}, context_instance=RequestContext(request))    

def explorer_example(request, method):
    return render_to_response('explorer_example.html', {'method' : method}, context_instance=RequestContext(request))    

def explorer_user_run(request):

    #make sure it's a post
    if not request.POST:
        raise Http404

    #build up the URL
    uri = request.POST['uri'] + '/?'
    uri += 'explorer_user_run=1'    
    post_items = request.POST.items()
    for post_key, post_value in post_items:
        if post_key != 'uri' and post_value:
            uri += ('&' + post_key + '=' + urllib.quote_plus(post_value))

    # Grab the API response
    result = urllib.urlopen(uri).read()

    return render_to_response('explorer_user_run.html', {'result' : result}, context_instance=RequestContext(request))    