from django.template import RequestContext, loader, Context
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from django.contrib.auth.decorators import login_required

from models import api_key
from forms import applyForm    

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
    
def explore_scraper_search(request):
    #If we ever progress to version 2.0, then pass the version number in to this function and render a different template
    # don't be tempted to just copy and paste it
    return render_to_response('scraper_search_1.0.html', {'keys' : 'test'}, context_instance=RequestContext(request))
    
    