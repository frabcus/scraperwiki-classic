from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from settings import MAX_API_ITEMS, API_DOMAIN

from django.contrib.auth.decorators import login_required

from models import api_key
from forms import applyForm

import urllib

def keys(request):
    
    user = request.user
    if not user.is_authenticated():
        # We need to have a valid user before we can make an API key
        request.notifications.add("You need to sign in or create an account before you can request an API key")
        return HttpResponseRedirect(reverse('login') + "?next=%s" % request.path_info)

    users_keys = api_key.objects.filter(user=user)

    key = api_key(user=user)
    form = applyForm(request.POST, instance=key)

    if request.POST:
        form.save(commit=False)
        form.save()
        return HttpResponseRedirect(request.path_info)

    return render_to_response('keys.html', 
    {
    'keys' : users_keys,
    'form' : form
    },
    context_instance=RequestContext(request))

def explore_scraper_search_1_0(request):
    return render_to_response('scraper_search_1.0.html', {'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getinfo')}, context_instance=RequestContext(request))

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
    return render_to_response('scraper_getdatabydate_1.0.html', {'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabydate')}, context_instance=RequestContext(request))    

def explore_scraper_getdatabylocation_1_0(request):
    return render_to_response('scraper_getdatabylocation_1.0.html', {'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabylocation')}, context_instance=RequestContext(request))    

def explorer_example(request, method):
    return render_to_response('explorer_example.html', {'method' : method}, context_instance=RequestContext(request))    
    
def explorer_user_run(request):
    
    #make sure it's a post
    if not request.POST:
        raise Http404

    #build up the URL
    uri = request.POST['uri']
    uri += "&".join("%s=%s" % (k,v) for k,v in request.POST.__dict__.items())
    uri += '&explorer_user_run=1'
    result= urllib.urlopen(uri).read()
    return render_to_response('explorer_user_run.html', {'result' : result}, context_instance=RequestContext(request))    