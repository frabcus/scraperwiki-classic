from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.conf import settings

from scraper import models
from scraper import forms
from scraper.forms import SearchForm
from api.emitters import CSVEmitter
import vc

import frontend

import subprocess

import StringIO, csv, types
import datetime
import urllib

try:                import json
except ImportError: import simplejson as json


def overview(request, scraper_short_name):
    """
    Shows info on the scraper plus example data.
    """
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects,
        short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_contributors = scraper.contributors()
    scraper_tags = Tag.objects.get_for_object(scraper)

    try:    offset = int(request.GET.get('i', 0))
    except ValueError:   offset = 0

    table = models.Scraper.objects.data_summary(
        scraper_id=scraper.guid,
        limit=1,
        offset=offset)
    data = None
    has_data = len(table['rows']) > 0
    if has_data:
        data = zip(table['headings'], table['rows'][0])

    chart_url = scraper.get_metadata('chart', '')
    if not chart_url.startswith('http://chart.apis.google.com/chart?'):
        chart_url = None

    return render_to_response('scraper/overview.html', {
        'scraper_tags': scraper_tags,
        'selected_tab': 'overview',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        'has_data': has_data,
        'data': data,
        'scraper_contributors': scraper_contributors,
        'chart_url': chart_url,
        }, context_instance=RequestContext(request))

def scraper_admin(request, scraper_short_name):
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    #you can only get here if you are signed in
    if not user.is_authenticated():
        raise Http404

    if request.method == 'POST':
        form = forms.ScraperAdministrationForm(request.POST, instance=scraper)
        if form.is_valid():
            s = form.save()
            s.tags = form.cleaned_data['tags']
    else:
        form = forms.ScraperAdministrationForm(instance=scraper)
            # somehow the magic that can convert from comma separated tags into the tags list is not able to convert back, hence this code.  can't be true
        form.fields['tags'].initial = ", ".join([tag.name for tag in scraper.tags])

    return render_to_response('scraper/admin.html', {
      'selected_tab': 'admin',
      'scraper': scraper,
      'user_owns_it': user_owns_it,
      'user_follows_it': user_follows_it,
      'form': form,
      }, context_instance=RequestContext(request))

def scraper_delete_data(request, scraper_short_name):
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    if scraper.owner() != request.user:
        raise Http404

    if request.POST.get('delete_data', None) == '1':
        models.Scraper.objects.clear_datastore(scraper_id=scraper.guid)

    return HttpResponseRedirect(reverse('scraper_admin', args=[scraper_short_name]))

def scraper_delete_scraper(request, scraper_short_name):
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    if scraper.owner() != request.user:
        raise Http404

    if request.POST.get('delete_scraper', None) == '1':
        scraper.deleted = True
        scraper.save()
        request.notifications.add("Your scraper has been deleted")
        return HttpResponseRedirect('/')

    return HttpResponseRedirect(reverse('scraper_admin', args=[scraper_short_name]))


def scraper_data(request, scraper_short_name):
    #user details
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    num_data_points = scraper.get_metadata('num_data_points')
    if type(num_data_points) != types.IntType:
        num_data_points = settings.MAX_DATA_POINTS

    column_order = scraper.get_metadata('data_columns')
    if not user_owns_it:
        private_columns = scraper.get_metadata('private_columns')
    else:
        private_columns = None

    #get data for this scaper
    data = models.Scraper.objects.data_summary(scraper_id=scraper.guid,
                                               limit=num_data_points, 
                                               column_order=column_order,
                                               private_columns=private_columns)

    # replicates output from data_summary_tables
    data_tables = {"": data }
    has_data = len(data['rows']) > 0

    return render_to_response('scraper/data.html', {
      'scraper_tags': scraper_tags,
      'selected_tab': 'data',
      'scraper': scraper,
      'user_owns_it': user_owns_it,
      'user_follows_it': user_follows_it,
      'data_tables': data_tables,
      'has_data': has_data,
      }, context_instance=RequestContext(request))


def scraper_map(request, scraper_short_name, map_only=False):
    #user details
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    num_map_points = scraper.get_metadata('num_map_points')
    if type(num_map_points) != types.IntType:
        num_map_points = settings.MAX_MAP_POINTS

    column_order = scraper.get_metadata('map_columns')
    if not user_owns_it:
        private_columns = scraper.get_metadata('private_columns')
    else:
        private_columns = None

    #get data for this scaper
    data = models.Scraper.objects.data_summary(scraper_id=scraper.guid,
                                               limit=num_map_points,
                                               column_order=column_order,
                                               private_columns=private_columns)
    has_data = len(data['rows']) > 0
    data = json.dumps(data)

    if map_only:
        template = 'scraper/map_only.html'
    else:
        template = 'scraper/map.html'

    return render_to_response(template, {
    'scraper_tags': scraper_tags,
    'selected_tab': 'map',
    'scraper': scraper,
    'user_owns_it': user_owns_it,
    'user_follows_it': user_follows_it,
    'data': data,
    'has_data': has_data,
    'has_map': True,
    }, context_instance=RequestContext(request))


# saved_code to go
# also make the diff with previous version and make the selection
# check that all the non-loggedin logic still works

def code(request, scraper_short_name):
    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    
    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1
    
    mercurialinterface = vc.MercurialInterface()
    status = mercurialinterface.getstatus(scraper, rev)
    
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    dictionary = { 'scraper_tags': scraper_tags, 'selected_tab': 'code', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }
                   
    # overcome lack of subtract in template
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        status["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]
        
    dictionary["status"] = status
    dictionary["line_count"] = status["code"].count("\n") + 3

    return render_to_response('scraper/code.html', dictionary, context_instance=RequestContext(request))


def comments(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()

    scraper_tags = Tag.objects.get_for_object(scraper)

    dictionary = { 'scraper_tags': scraper_tags, 'scraper_owner': scraper_owner, 'scraper_contributors': scraper_contributors,
                   'scraper_followers': scraper_followers, 'selected_tab': 'comments', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }
    return render_to_response('scraper/comments.html', dictionary, context_instance=RequestContext(request))


def scraper_history(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    
    # sift through the alerts filtering on the scraper through the annoying content_type field
    content_type = scraper.content_type()
    history = frontend.models.Alerts.objects.filter(content_type=content_type, object_id=scraper.pk).order_by('-datetime')
        
    dictionary = { 'selected_tab': 'history', 'scraper': scraper, 'history': history,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }
    
    # extract the commit log directly from the mercurial repository
    # (in future, the entries in django may be synchronized against this to make it possible to update the repository(ies) outside the system)
    commitlog = [ ]
    # should commit info about the saved   commitlog.append({"rev":commitentry['rev'], "description":commitentry['description'], "datetime":commitentry["date"], "user":user})
    mercurialinterface = vc.MercurialInterface()
    for commitentry in mercurialinterface.getcommitlog(scraper):
        try:    user = User.objects.get(pk=int(commitentry["userid"]))
        except: user = None
        commitlog.append({"rev":commitentry['rev'], "description":commitentry['description'], "datetime":commitentry["date"], "user":user})
    commitlog.reverse()
    dictionary["commitlog"] = commitlog
    dictionary["filestatus"] = mercurialinterface.getfilestatus(scraper)
    
    return render_to_response('scraper/history.html', dictionary, context_instance=RequestContext(request))


def export_csv(request, scraper_short_name):
    """
    This could have been done by having linked directly to the api/csvout, but
    difficult to make the urlreverse for something in a different app code here
    itentical to scraperwiki/web/api/emitters.py CSVEmitter render()
    """
    scraper = get_object_or_404(
        models.Scraper.objects,
        short_name=scraper_short_name)
    dictlist = models.Scraper.objects.data_dictlist(
        scraper_id=scraper.guid,
        limit=100000)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=%s.csv' % (scraper_short_name)
    response.write(CSVEmitter.to_csv(dictlist))

    return response
    #template = loader.get_template('scraper/data.csv')
    #context = Context({'data_tables': data_tables,})


def scraper_list(request, page_number):
    all_scrapers = models.Scraper.objects.filter(published=True).exclude(language='HTML').order_by('-created_at')

    # Number of results to show from settings
    paginator = Paginator(all_scrapers, settings.SCRAPERS_PER_PAGE)

    try:  
        page = int(page_number)
    except (ValueError, TypeError):
        page = 1
    
    if page == 1:
        featured_scrapers = models.Scraper.objects.filter(published=True, featured=True).exclude(language='HTML').order_by('-created_at')
    else:
        featured_scrapers = None
        

    # If page request (9999) is out of range, deliver last page of results.
    try:
        scrapers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        scrapers = paginator.page(paginator.num_pages)

    form = SearchForm()
    
    # put number of people here so we can see it
    #npeople = UserScraperEditing in models.UserScraperEditing.objects.all().count()
    # there might be a slick way of counting this, but I don't know it.
    npeople = len(set([userscraperediting.user  for userscraperediting in models.UserScraperEditing.objects.all() ]))
    dictionary = { "scrapers": scrapers, "form": form, "featured_scrapers":featured_scrapers, "npeople": npeople }
    return render_to_response('scraper/list.html', dictionary, context_instance=RequestContext(request))


def scraper_table(request):
    dictionary = { }
    dictionary["scrapers"] = models.Scraper.objects.filter(published=True).order_by('-created_at')
    dictionary["loggedinusers"] = set([ userscraperediting.user  for userscraperediting in models.UserScraperEditing.objects.filter(user__isnull=False)])
    dictionary["numloggedoutusers"] = models.UserScraperEditing.objects.filter(user__isnull=True).count()
    dictionary["numdraftscrapersediting"] = models.UserScraperEditing.objects.filter(scraper__isnull=True).count()
    dictionary["numpublishedscrapersediting"] = models.UserScraperEditing.objects.filter(scraper__published=True).count()
    dictionary["numunpublishedscrapersediting"] = models.UserScraperEditing.objects.filter(scraper__published=False).count()
    dictionary["numpublishedscraperstotal"] = dictionary["scrapers"].count()
    dictionary["numunpublishedscraperstotal"] = models.Scraper.objects.filter(published=False).count()
    dictionary["numdeletedscrapers"] = models.Scraper.unfiltered.filter(deleted=True).count()
    return render_to_response('scraper/scraper_table.html', dictionary, context_instance=RequestContext(request))
    


def download(request, scraper_short_name):
    """
    TODO: DELETE?
    """
    scraper = get_object_or_404(models.Scraper.objects, 
                                short_name=scraper_short_name)
    response = HttpResponse(scraper.saved_code(), mimetype="text/plain")
    response['Content-Disposition'] = \
        'attachment; filename=%s.py' % (scraper.short_name)
    return response


def all_tags(request):
    return render_to_response(
        'scraper/all_tags.html',
        context_instance = RequestContext(request))


def scraper_tag(request, tag):
    tag = get_tag(tag)
    scrapers = models.Scraper.objects.filter(published=True)
    queryset = TaggedItem.objects.get_by_model(scrapers, tag)
    return render_to_response('scraper/tag.html', {
        'queryset': queryset,
        'tag': tag,
        'selected_tab': 'items',
        }, context_instance=RequestContext(request))


def tag_data(request, tag):  # to delete
    assert False

    tag = get_tag(tag)
    scrapers = models.Scraper.objects.filter(published=True)
    queryset = TaggedItem.objects.get_by_model(scrapers, tag)

    guids = []
    for q in queryset:
        guids.append(q.guid)
    data = models.Scraper.objects.data_summary(scraper_id=guids)

    return render_to_response('scraper/tag_data.html', {
        'data': data,
        'tag': tag,
        'selected_tab': 'data',
        }, context_instance=RequestContext(request))


def search(request, q=""):
    if (q != ""):
        form = SearchForm(initial={'q': q})
        q = q.strip()

        scrapers = models.Scraper.objects.search(q)
        return render_to_response('scraper/search_results.html',
            {
                'scrapers': scrapers,
                'form': form,
                'query': q,},
            context_instance=RequestContext(request))

    # If the form has been submitted, or we have a search term in the URL
    # - redirect to nice URL
    elif (request.POST):
        form = SearchForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data['q']
            # Process the data in form.cleaned_data
            # Redirect after POST
            return HttpResponseRedirect('/scrapers/search/%s/' % urllib.quote(q.encode('utf-8')))
        else:
            form = SearchForm()
            return render_to_response('scraper/search.html', {
                'form': form,},
                context_instance=RequestContext(request))
    else:
        form = SearchForm()
        return render_to_response('scraper/search.html', {
            'form': form,
        }, context_instance = RequestContext(request))


def follow (request, scraper_short_name):
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user = request.user
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    # add the user to follower list
    scraper.add_user_role(user, 'follow')
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)


def unfollow(request, scraper_short_name):
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user = request.user
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    # remove the user from follower list
    scraper.unfollow(user)
    # Redirect after POST
    return HttpResponseRedirect('/scrapers/show/%s/' % scraper.short_name)


def twisterstatus(request):
    if 'value' not in request.POST:
        return HttpResponse("needs value=")
    tstatus = json.loads(request.POST.get('value'))
    
    twisterclientnumbers = set()  # used to delete the ones that no longer exist
    
    # we are making objects in django to represent the objects in twister for editor windows open
    for client in tstatus["clientlist"]:
        # fixed attributes of the object
        twisterclientnumber = client["clientnumber"]
        twisterclientnumbers.add(twisterclientnumber)
        try:
            user = client['username'] and User.objects.get(username=client['username']) or None
            scraper = client['guid'] and models.Scraper.objects.get(guid=client['guid']) or None
        except:
            continue
        
        # identify or create the editing object
        try:
            userscraperediting = models.UserScraperEditing.objects.create(user=user, scraper=scraper, twisterclientnumber=twisterclientnumber)
            userscraperediting.editingsince = datetime.datetime.now()
        except IntegrityError:
            userscraperediting = models.UserScraperEditing.objects.get(twisterclientnumber=twisterclientnumber)

        assert models.UserScraperEditing.objects.filter(twisterclientnumber=twisterclientnumber).count() == 1, client
        
        # updateable values of the object
        userscraperediting.twisterscraperpriority = client['scrapereditornumber']
        
        # this condition could instead reference a running object
        if client['running'] and not userscraperediting.runningsince:
            userscraperediting.runningsince = datetime.datetime.now()
        if not client['running'] and userscraperediting.runningsince:
            userscraperediting.runningsince = None
        
        userscraperediting.save()

    # discard now closed values of the object
    for userscraperediting in models.UserScraperEditing.objects.all():
        if userscraperediting.twisterclientnumber not in twisterclientnumbers:
            userscraperediting.delete()
            # or could use the field: closedsince  = models.DateTimeField(blank=True, null=True)
    return HttpResponse("Howdy ppp ")


# quick hack the manage the RPC execute feature 
# to test this locally you need to use python manage.py runserver twice, on 8000 and on 8010, 
# and view the webpage on 8010
def rpcexecute(request, scraper_short_name):
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    runner_path = "%s/runner.py" % settings.FIREBOX_PATH
    failed = False

    rargs = { }
    for key in request.POST.keys():
        rargs[str(key)] = request.POST.get(key)
    for key in request.GET.keys():
        rargs[str(key)] = request.GET.get(key)
    func = rargs.pop("function", None)
    for key in rargs.keys():
        try: 
            rargs[key] = json.loads(rargs[key])
        except:
            pass

    args = [runner_path]
    args.append('--guid=%s' % scraper.guid)
    args.append('--language=%s' % scraper.language.lower())
    args.append('--name=%s' % scraper.short_name)
    args.append('--cpulimit=80')
    
    runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    runner.stdin.write(scraper.saved_code())
    
    # append in the single line at the bottom that gets the rpc executed with the right function and arguments
    if func:
        runner.stdin.write("\n\n%s(**%s)\n" % (func, repr(rargs)))
        
    runner.stdin.close()

    response = HttpResponse()
    for line in runner.stdout:
        try:
            message = json.loads(line)
            print "mmmm", message
            if message['message_type'] == 'fail':
                failed = True
            elif message['message_type'] == 'exception':
                response.write("<h3>%s</h3>\n" % str(message["jtraceback"].get("exceptiondescription")).replace("<", "&lt;"))
                for stackentry in message["jtraceback"]["stackdump"]:
                    response.write("<h3>%s</h3>\n" % re.replace("<", "&lt;", str(stackentry).replace("<", "&lt;")))
            
            # recover the message from all the escaping
            if message['message_type'] == "console" and message.get('message_sub_type') != 'consolestatus':
                response.write(message["content"])
        
        except:
            pass
        
    return response
    

def htmlview(request, scraper_short_name):
    scraper = get_object_or_404(models.Scraper.objects, short_name=scraper_short_name)
    return HttpResponse(scraper.saved_code())

def run_event(request, event_id):
    event = get_object_or_404(models.ScraperRunEvent, id=event_id)
    return render_to_response('scraper/run_event.html', {'event': event}, context_instance=RequestContext(request))

def commit_event(request, event_id):
    event = get_object_or_404(models.ScraperCommitEvent, id=event_id)
    return render_to_response('scraper/commit_event.html', {'event': event}, context_instance=RequestContext(request))

def running_scrapers(request):
    events = models.ScraperRunEvent.objects.filter(run_ended=None)
    return render_to_response('scraper/running_scrapers.html', {'events': events}, context_instance=RequestContext(request))
