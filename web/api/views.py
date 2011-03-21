import urllib
import urllib2

from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from settings import MAX_API_ITEMS, API_DOMAIN

from codewiki.models import Scraper, Code
from external.datastore import Datastore

from django.contrib.auth.decorators import login_required

from models import api_key
from forms import applyForm

# The API explorer requires two connections to the server, which is not supported by manage.py runserver
# To run locally, you need to ensure that settings.py contains API_DOMAIN = 'localhost:8010'
# and you run the server twice in two separate shells
#python manage.py runserver 8000
#python manage.py runserver 8010
# And then you use browse at http://localhost:8000/api/1.0/explore/scraperwiki.scraper.getinfo

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

    return render_to_response('api/keys.html', {'keys' : users_keys,'form' : form}, context_instance=RequestContext(request))

def example_scrapers(user, count):
    if user.is_authenticated():
        scrapers = user.code_set.filter(usercoderole__role='owner', deleted=False, published=True).order_by('-first_published_at')[:count]
    else:
        scrapers = Code.objects.filter(deleted=False, featured=True).order_by('-first_published_at')[:count]
    
    return scrapers

def explore_scraper_search_1_0(request):
    user = request.user
    users_keys = api_key.objects.filter(user=user)
    
    return render_to_response('api/scraper_search_1.0.html', {'keys' : users_keys, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_search')}, context_instance=RequestContext(request))

def explore_scraper_getinfo_1_0(request):
    short_name = request.GET.get('name', '')
    user = request.user
    scrapers = example_scrapers(user, 5)
    users_keys = api_key.objects.filter(user=user)
    return render_to_response('api/scraper_getinfo_1.0.html', {'keys' : users_keys, 'scrapers': scrapers, 'has_scrapers': True, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getinfo'), "short_name":short_name}, context_instance=RequestContext(request))

def explore_scraper_getruninfo_1_0(request):
    short_name = request.GET.get('name', '')
    user = request.user
    scrapers = example_scrapers(user, 5)
    users_keys = api_key.objects.filter(user=user)
    return render_to_response('api/scraper_getruninfo_1.0.html', {'keys' : users_keys, 'scrapers': scrapers, 'has_scrapers': True, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getruninfo'), "short_name":short_name}, context_instance=RequestContext(request))

def explore_scraper_getuserinfo_1_0(request):
    user = request.user
    users = list(User.objects.all().order_by('-date_joined')[:5])
    if user.is_authenticated() and user not in users:
        users.insert(0, user)
    users_keys = api_key.objects.filter(user=user)
    return render_to_response('api/scraper_getuserinfo_1.0.html', {'keys' : users_keys, 'users': users, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getuserinfo')}, context_instance=RequestContext(request))


def explore_scraper_getkeys_1_0(request):
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)

    return render_to_response('api/datastore_getkeys_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getkeys')}, context_instance=RequestContext(request))

def explore_datastore_search_1_0(request):
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)

    return render_to_response('api/datastore_search_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_datastore_search')}, context_instance=RequestContext(request))

def explore_scraper_getdata_1_0(request):
    short_name = request.GET.get('name', '')
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)
    return render_to_response('api/scraper_getdata_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdata'), 'short_name': short_name}, context_instance=RequestContext(request))

def explore_scraper_sqlite_1_0(request):
    short_name = request.GET.get('name', '')
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)
    return render_to_response('api/datastore_sqlite_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_sqlite'), 'short_name': short_name}, context_instance=RequestContext(request))

def explore_scraper_getdatabydate_1_0(request):
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)
    return render_to_response('api/scraper_getdatabydate_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabydate')}, context_instance=RequestContext(request))    

def explore_scraper_getdatabylocation_1_0(request):
    scrapers = []
    user = request.user
    scrapers = example_scrapers(user, 5)
        
    return render_to_response('api/scraper_getdatabylocation_1.0.html', {'scrapers': scrapers, 'has_scrapers': True, 'max_api_items': MAX_API_ITEMS, 'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_getdatabylocation')}, context_instance=RequestContext(request))    

def explore_geo_postcodetolatlng_1_0(request):
    return render_to_response('api/geo_postcodetolatlng_1.0.html', {'api_domain': API_DOMAIN, 'api_uri': reverse('api:method_geo_postcode_to_latlng')}, context_instance=RequestContext(request))    




def explorer_user_run(request):
    #make sure it's a post
    if not request.POST:
        return HttpResponseNotFound('Must be a POST request')
    
    #build up the URL
    post_data = dict(request.POST)
    for k,v in post_data.items():
        if not v[0]: 
            del post_data[k]

    uri = post_data.pop('uri')[0]
    post_data['explorer_user_run'] = ['1']

    querystring = urllib.urlencode([(k.encode('utf-8'),v[0].encode('utf-8')) for k,v in post_data.items()])
    url = "%s?%s" % (uri, querystring)
    
    # Grab the API response
    result = urllib2.urlopen(url).read()
    
    return render_to_response('api/explorer_user_run.html', 
                              {'result' : result}, 
                              context_instance=RequestContext(request))

# fills in that black iframe initially (prob was supposed to have further documentation)
def explorer_example(request, method):
    return render_to_response('api/explorer_example.html', {'method' : method}, context_instance=RequestContext(request))    


