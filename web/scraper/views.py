from django.template import RequestContext, loader, Context
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag
from django.conf import settings

from scraper import models
from scraper import forms
from scraper.forms import SearchForm

import re

def create(request):
    if request.method == 'POST':
        return render_to_response('scraper/create.html', {}, context_instance=RequestContext(request)) 
    else:
        return render_to_response('scraper/create.html', {}, context_instance=RequestContext(request)) 

def data (request, scraper_short_name):
    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    data_tables = models.Scraper.objects.data_summary_tables(scraper_id=scraper.guid, limit=1000)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)
    
    return render_to_response('scraper/data.html', {
      'scraper_tags' : scraper_tags,
      'selected_tab': 'data', 
      'scraper': scraper, 
      'user_owns_it': user_owns_it, 
      'user_follows_it': user_follows_it,
      'data_tables' : data_tables,
      }, context_instance=RequestContext(request))


def code (request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    
    scraper_tags = Tag.objects.get_for_object(scraper)
    
    return render_to_response('scraper/code.html', {
        'scraper_tags' : scraper_tags,
        'selected_tab': 'code', 
        'scraper': scraper, 
        'user_owns_it': user_owns_it, 
        'user_follows_it': user_follows_it
        }, context_instance=RequestContext(request))

def contributors (request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    
    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()
    
    scraper_tags = Tag.objects.get_for_object(scraper)
    
    return render_to_response('scraper/contributers.html', {
        'scraper_tags' : scraper_tags,
        'scraper_owner' : scraper_owner,
        'scraper_contributors' : scraper_contributors,
        'scraper_followers' : scraper_followers,
        'selected_tab': 'contributors', 
        'scraper': scraper, 
        'user_owns_it': user_owns_it, 
        'user_follows_it': user_follows_it
        }, context_instance=RequestContext(request))
        
def comments (request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    
    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()
    
    scraper_tags = Tag.objects.get_for_object(scraper)
    
    return render_to_response('scraper/comments.html', {
        'scraper_tags' : scraper_tags,
        'scraper_owner' : scraper_owner,
        'scraper_contributors' : scraper_contributors,
        'scraper_followers' : scraper_followers,
        'selected_tab': 'comments', 
        'scraper': scraper, 
        'user_owns_it': user_owns_it, 
        'user_follows_it': user_follows_it
        }, context_instance=RequestContext(request))


def show(request, scraper_short_name, selected_tab = 'data'):
    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    you_own_it = (scraper.owner() == user)
    you_follow_it = (user in scraper.followers())
    data = models.scraperData.objects.summary()
    tabs = [
	  {'code': 'data', 'title': 'Data',       'template': 'scraper/data_tab.html'},
	  {'code': 'code', 'title': 'Code',       'template': 'scraper/code_tab.html'},
	  {'code': 'hist', 'title': 'History',    'template': 'scraper/hist_tab.html'},
	  {'code': 'disc', 'title': 'Discussion', 'template': 'scraper/disc_tab.html'},
	  {'code': 'developers', 'title': 'Developers',    'template': 'scraper/edit_tab.html'}
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

    return render_to_response('scraper/show.html', {'data' : data, 'selected_tab': selected_tab, 'scraper': scraper, 'you_own_it': you_own_it, 'you_follow_it': you_follow_it, 'tabs': tabs, 'tab_to_show': tab_to_show}, context_instance=RequestContext(request))


# would be better to use the python csv writer as an generator and pass it straight as a response -- without the use of a template
# also could allow for individual tables to be output (multiple links on the data page, for example)
def export_csv (request, scraper_short_name):
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    data_tables = models.Scraper.objects.data_summary_tables(scraper_id=scraper.guid, limit=1000000)  # maybe limit=0 should be unlimited (or add limits everywhere)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % (scraper_short_name)

    template = loader.get_template('scraper/data.csv')
    context = Context({'data_tables': data_tables,})

    response.write(template.render(context))
    return response
    
    
def list(request):
    #scrapers = models.Scraper.objects.filter(published=True).order_by('-created_at')
    #return render_to_response('scraper/list.html', {'scrapers': scrapers}, context_instance = RequestContext(request))

    scraper_list = models.Scraper.objects.filter(published=True).order_by('-created_at')
    paginator = Paginator(scraper_list, settings.SCRAPERS_PER_PAGE) # Number of results to show from settings

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        scrapers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        scrapers = paginator.page(paginator.num_pages)

    form = SearchForm()
        
    return render_to_response('scraper/list.html', {"scrapers": scrapers, "form": form, })
    
def download(request, scraper_id = 0):
    user = request.user
    scraper = get_object_or_404(models.Scraper.objects,id=scraper_id)
    response = HttpResponse(scraper.current_code(), mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s.py' % (scraper.short_name)
    return response


def all_tags(request):
    return render_to_response('scraper/all_tags.html', context_instance = RequestContext(request))
    
    
def tag(request, tag):
    from tagging.utils import get_tag
    from tagging.models import Tag, TaggedItem
    
    tag = get_tag(tag)
    scrapers = models.Scraper.objects.filter(published=True)    
    queryset = TaggedItem.objects.get_by_model(scrapers, tag)
    return render_to_response('scraper/tag.html', {
        'queryset': queryset, 
        'tag' : tag,
        'selected_tab' : 'items',
        }, context_instance = RequestContext(request))
    
def tag_data(request, tag):
    from tagging.utils import get_tag
    from tagging.models import Tag, TaggedItem
    
    tag = get_tag(tag)
    scrapers = models.Scraper.objects.filter(published=True)
    queryset = TaggedItem.objects.get_by_model(scrapers, tag)
    
    guids = []
    for q in queryset:
        guids.append(q.guid)
    data = models.Scraper.objects.data_summary(scraper_id=guids)
    count = models.Scraper.objects.item_count_for_tag(guids=guids)
    
    return render_to_response('scraper/tag_data.html', {
        'data': data, 
        'tag' : tag,
        'selected_tab' : 'data',
        }, context_instance = RequestContext(request))
    
        
def search(request, q=""):
    if (q != ""): 
        form = SearchForm(initial={'q': q})
        q = q.strip()
        scrapers = models.Scraper.objects.filter(title__icontains=q, published=True) 
        # and by tag
        tag = Tag.objects.filter(name__icontains=q)
        if tag: 
          qs = TaggedItem.objects.get_by_model(models.Scraper, tag)
          scrapers = scrapers | qs
        else: 
          qs = None
        #Only show published scrapers, sort by creation date
        scrapers = scrapers.filter(published=True)
        scrapers = scrapers.order_by('-created_at')
        return render_to_response('scraper/search_results.html',
          {'scrapers': scrapers,  'form': form, 'query': q})
    elif (request.POST): # If the form has been submitted, or we have a search term in the URL
        form = SearchForm(request.POST) 
        if form.is_valid(): 
          q = form.cleaned_data['q']
          # Process the data in form.cleaned_data
          return HttpResponseRedirect('/scrapers/search/%s/' % q) # Redirect after POST
        else:
          form = SearchForm() 
          return render_to_response('scraper/search.html', {
            'form': form,
          })
    else:
        form = SearchForm()
        return render_to_response('scraper/search.html', {
            'form': form,
        })
    
def follow (request, scraper_short_name):
	scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
	user = request.user
	user_owns_it = (scraper.owner() == user)
	user_follows_it = (user in scraper.followers())
    # add the user to follower list
	scraper.add_user_role(user, 'follow')

	return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name) # Redirect after POST
    
def unfollow(request, scraper_short_name):
	scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
	user = request.user
	user_owns_it = (scraper.owner() == user)
	user_follows_it = (user in scraper.followers())
	# remove the user from follower list
	scraper.unfollow(user)
 	
	return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name) # Redirect after POST