from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag
from django.db import IntegrityError
from django.contrib.auth.models import User
import textile

from django.conf import settings

from codewiki import models
from codewiki import forms
from codewiki.forms import ChooseTemplateForm
from api.emitters import CSVEmitter 
import vc
import frontend

import subprocess

import StringIO, csv, types
import datetime

try:                import json
except ImportError: import simplejson as json


def scraper_overview(request, scraper_short_name):
    """
    Shows info on the scraper plus example data.
    """
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects,
        short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))
    
    #get views that use this scraper
    related_views = scraper.relations.filter(wiki_type='view')
    
    #get meta data
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_contributors = scraper.contributors()
    scraper_tags = Tag.objects.get_for_object(scraper)

    num_data_points = scraper.get_metadata('num_data_points')
    if type(num_data_points) != types.IntType:
        num_data_points = 50

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
    return render_to_response('codewiki/overview.html', {
        'scraper_tags': scraper_tags,
        'selected_tab': 'overview',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        'has_data': has_data,
        'data': data,
        'scraper_contributors': scraper_contributors,
        'related_views': related_views,
        }, context_instance=RequestContext(request))

def view_admin (request, short_name):
    response = None

    user = request.user
    view = get_object_or_404(
        models.View.objects, short_name=short_name)
    user_owns_it = (view.owner() == user)

    form = forms.ViewAdministrationForm(instance=view)
    #form.fields['tags'].initial = ", ".join([tag.name for tag in view.tags])
    response = render_to_response('codewiki/view_admin.html', {'selected_tab': 'overview','scraper': view,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    #you can only get here if you are signed in
    if not user.is_authenticated():
        raise Http404

    if request.method == 'POST':
        #is this an ajax post of a single value?
        js = request.POST.get('js', None)
        #single fields saved via ajax
        if js:
            response = HttpResponse()
            response_text = ''
            element_id = request.POST.get('id', None)       
            if element_id == 'divAboutScraper':
                view.description = request.POST.get('value', None)                                                  
                response_text = textile.textile(view.description)

            if element_id == 'hCodeTitle':
                view.title = request.POST.get('value', None)                                                  
                response_text = view.title

            if element_id == 'divEditTags':
                view.tags = ", ".join([tag.name for tag in view.tags]) + ',' + request.POST.get('value', '')                                                  
                response_text = ", ".join([tag.name for tag in view.tags])

            #save view
            view.save()
            response.write(response_text)
        #saved by form 
        else:
            form = forms.ViewAdministrationForm(request.POST, instance=view)
            response =  HttpResponseRedirect(reverse('view_overview', args=[short_name]))

            if form.is_valid():
                s = form.save()
                s.tags = form.cleaned_data['tags']
            else:
                response = render_to_response('codewiki/admin.html', {'selected_tab': 'overview','scraper': view,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    # send back whatever responbse we have
    return response
    
def scraper_admin (request, short_name):
    response = None

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=short_name)
    user_owns_it = (scraper.owner() == user)

    form = forms.ScraperAdministrationForm(instance=scraper)
    form.fields['tags'].initial = ", ".join([tag.name for tag in scraper.tags])
    response = render_to_response('codewiki/admin.html', {'selected_tab': 'overview','scraper': scraper,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    #you can only get here if you are signed in
    if not user.is_authenticated():
        raise Http404

    if request.method == 'POST':
        #is this an ajax post of a single value?
        js = request.POST.get('js', None)
        #single fields saved via ajax
        if js:
            response = HttpResponse()
            response_text = ''
            element_id = request.POST.get('id', None)       
            if element_id == 'divAboutScraper':
                scraper.description = request.POST.get('value', None)                                                  
                response_text = textile.textile(scraper.description)
                
            if element_id == 'hCodeTitle':
                scraper.title = request.POST.get('value', None)                                                  
                response_text = scraper.title

            if element_id == 'divEditTags':
                scraper.tags = ", ".join([tag.name for tag in scraper.tags]) + ',' + request.POST.get('value', '')                                                  
                response_text = ", ".join([tag.name for tag in scraper.tags])

            #save scraper
            scraper.save()
            response.write(response_text)
        #saved by form 
        else:
            form = forms.ScraperAdministrationForm(request.POST, instance=scraper)
            response =  HttpResponseRedirect(reverse('scraper_overview', args=[short_name]))

            if form.is_valid():
                s = form.save()
                s.tags = form.cleaned_data['tags']
            else:
                response = render_to_response('codewiki/admin.html', {'selected_tab': 'overview','scraper': scraper,'user_owns_it': user_owns_it, 'form': form,}, context_instance=RequestContext(request))

    # send back whatever responbse we have
    return response
    
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



def scraper_map(request, scraper_short_name, map_only=False):
    #user details
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

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
        template = 'codewiki/map_only.html'
    else:
        template = 'codewiki/map.html'

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


def view_overview (request, short_name):
    user = request.user
    scraper = get_object_or_404(models.View.objects, short_name=short_name)
    
    #get scrapers used in this view
    related_scrapers = scraper.relations.filter(wiki_type='scraper')
    
    return render_to_response('codewiki/view_overview.html', {'selected_tab': 'overview', 'scraper': scraper, 'related_scrapers': related_scrapers, }, context_instance=RequestContext(request))
    
    
def view_fullscreen (request, short_name):
    user = request.user
    scraper = get_object_or_404(models.View.objects, short_name=short_name)

    return render_to_response('codewiki/view_fullscreen.html', {'scraper': scraper}, context_instance=RequestContext(request))

def comments(request, wiki_type, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Code.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()

    scraper_tags = Tag.objects.get_for_object(scraper)

    dictionary = { 'scraper_tags': scraper_tags, 'scraper_owner': scraper_owner, 'scraper_contributors': scraper_contributors,
                   'scraper_followers': scraper_followers, 'selected_tab': 'comments', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }
    return render_to_response('codewiki/comments.html', dictionary, context_instance=RequestContext(request))


def scraper_history(request, wiki_type, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(models.Code.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

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
    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    for commitentry in mercurialinterface.getcommitlog(scraper):
        try:    user = User.objects.get(pk=int(commitentry["userid"]))
        except: user = None
        commitlog.append({"rev":commitentry['rev'], "description":commitentry['description'], "datetime":commitentry["date"], "user":user})
    commitlog.reverse()
    dictionary["commitlog"] = commitlog
    dictionary["filestatus"] = mercurialinterface.getfilestatus(scraper)
    
    return render_to_response('codewiki/history.html', dictionary, context_instance=RequestContext(request))

def code(request, wiki_type, scraper_short_name):
    user = request.user
    scraper = get_object_or_404(models.Code.objects, short_name=scraper_short_name)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('scraper/access_denied_unpublished.html', context_instance=RequestContext(request))

    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1

    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    status = mercurialinterface.getstatus(scraper, rev)

    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    dictionary = { 'scraper_tags': scraper_tags, 'selected_tab': 'history', 'scraper': scraper,
                   'user_owns_it': user_owns_it, 'user_follows_it': user_follows_it }

    # overcome lack of subtract in template
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        status["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]

    dictionary["status"] = status
    dictionary["line_count"] = status["code"].count("\n") + 3

    return render_to_response('codewiki/code.html', dictionary, context_instance=RequestContext(request))

def raw_about_markup(request, wiki_type, short_name):
    code_object = get_object_or_404(models.Code.objects, short_name=short_name)
    response = HttpResponse(mimetype='text/x-web-textile')
    response.write(code_object.description)
    return response



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
    #template = loader.get_template('codewiki/data.csv')
    #context = Context({'data_tables': data_tables,})


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
    return render_to_response('codewiki/scraper_table.html', dictionary, context_instance=RequestContext(request))
    


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
        'codewiki/all_tags.html',
        context_instance = RequestContext(request))


def scraper_tag(request, tag):
    tag = get_tag(tag)
    scrapers = models.Scraper.objects.filter(published=True)
    queryset = TaggedItem.objects.get_by_model(scrapers, tag)
    return render_to_response('codewiki/tag.html', {
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

    return render_to_response('codewiki/tag_data.html', {
        'data': data,
        'tag': tag,
        'selected_tab': 'data',
        }, context_instance=RequestContext(request))

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


def rpcexecute_dummy(request, scraper_short_name, revision = None):
    response = HttpResponse()
    response.write('''
    <html>
      <head>
        <script type='text/javascript' src='http://www.google.com/jsapi'></script>
        <script type='text/javascript'>
          google.load('visualization', '1', {'packages':['annotatedtimeline']});
          google.setOnLoadCallback(drawChart);
          function drawChart() {
            var data = new google.visualization.DataTable();
            data.addColumn('date', 'Date');
            data.addColumn('number', 'Sold Pencils');
            data.addColumn('string', 'title1');
            data.addColumn('string', 'text1');
            data.addColumn('number', 'Sold Pens');
            data.addColumn('string', 'title2');
            data.addColumn('string', 'text2');
            data.addRows([
              [new Date(2008, 1 ,1), 30000, undefined, undefined, 40645, undefined, undefined],
              [new Date(2008, 1 ,2), 14045, undefined, undefined, 20374, undefined, undefined],
              [new Date(2008, 1 ,3), 55022, undefined, undefined, 50766, undefined, undefined],
              [new Date(2008, 1 ,4), 75284, undefined, undefined, 14334, 'Out of Stock','Ran out of stock on pens at 4pm'],
              [new Date(2008, 1 ,5), 41476, 'Bought Pens','Bought 200k pens', 66467, undefined, undefined],
              [new Date(2008, 1 ,6), 33322, undefined, undefined, 39463, undefined, undefined]
            ]);

            var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('chart_div'));
            chart.draw(data, {displayAnnotations: true});
          }
        </script>
      </head>

      <body style="height:10000px;">
        <div id='chart_div' style='width: 700px; height: 240px;'></div>

      </body>
    </html>
    '''
    )
    print "fdsfdsdfs"
    return response
                        
# quick hack the manage the RPC execute feature 
# to test this locally you need to use python manage.py runserver twice, on 8000 and on 8010, 
# and view the webpage on 8010
def rpcexecute(request, scraper_short_name, revision = None):
    
    if settings.USE_DUMMY_VIEWS == True:
        return rpcexecute_dummy(request, scraper_short_name, revision)
    
    scraper = get_object_or_404(models.View.objects, short_name=scraper_short_name)
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
    runner.stdin.write(scraper.saved_code(revision))
    
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
    view = get_object_or_404(models.View.objects, short_name=scraper_short_name)
    return HttpResponse(view.saved_code())

def run_event(request, event_id):
    event = get_object_or_404(models.ScraperRunEvent, id=event_id)
    return render_to_response('codewiki/run_event.html', {'event': event}, context_instance=RequestContext(request))

def commit_event(request, event_id):
    event = get_object_or_404(models.CodeCommitEvent, id=event_id)
    return render_to_response('codewiki/commit_event.html', {'event': event}, context_instance=RequestContext(request))

def running_scrapers(request):
    events = models.ScraperRunEvent.objects.filter(run_ended=None)
    return render_to_response('codewiki/running_scrapers.html', {'events': events}, context_instance=RequestContext(request))

def choose_template(request, wiki_type):
    form = forms.ChooseTemplateForm(wiki_type)
    return render_to_response('codewiki/ajax/choose_template.html', {'wiki_type': wiki_type, 'form': form}, context_instance=RequestContext(request))


def chosen_template(request, wiki_type):
    template = request.GET.get('template', None)
    language = request.GET.get('language', None)
    template_arg = ''
    if template:
        template_arg = '?template=' + template
    return HttpResponseRedirect(reverse('editor', args=(wiki_type, language)) + template_arg)
    
def delete_draft(request):
    if request.session.get('ScraperDraft', False):
        del request.session['ScraperDraft']
    #return HttpResponseRedirect(reverse('editor'))

def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if not code:
        return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')
    scraper = get_object_or_404(models.Code, short_name=short_name)
    result = '\n'.join(difflib.unified_diff(scraper.saved_code().splitlines(), code.splitlines(), lineterm=''))
    return HttpResponse("::::" + result, mimetype='text')

def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')
    scraper = get_object_or_404(models.Code, short_name=short_name)
    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        result = "%s:::sElEcT rAnGe:::%s" % (json.dumps(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        result = newcode
    return HttpResponse(result, mimetype="text/plain")

#save a code object
def save_code(code_object, user, code_text, bnew):

    # save the actual object to mySQL
    code_object.update_meta()
    code_object.line_count = int(code_text.count("\n"))
    code_object.save()   

    # save the code to mercurial
    mercurialinterface = vc.MercurialInterface(code_object.get_repo_path())
    mercurialinterface.save(code_object, code_text)
    rev = mercurialinterface.commit(code_object, message='', user=user)
    mercurialinterface.updatecommitalertsrev(rev)

    # Add user roles
    if code_object.owner():
        if code_object.owner().pk != user.pk:
            code_object.add_user_role(user, 'editor')
    else:
        code_object.add_user_role(user, 'owner')

# Handle Session Draft
# A non-served page for saving scrapers that have been stored in the session for non-signed in users
def handle_session_draft(request, action):

    # check if they are signed in, if no, they shouldent be here, off to the signin page
    if not request.user.is_authenticated():
        response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
        return HttpResponseRedirect(response_url)

    #check if anything in the session        
    session_scraper_draft = request.session.pop('ScraperDraft', None)

    # shouldn't be here
    if not session_scraper_draft:
        response_url = reverse('frontpage')
        return HttpResponseRedirect(response_url)

    draft_scraper = session_scraper_draft.get('scraper', None)
    draft_scraper.save()
    #draft_commit_message = action.startswith('commit') and session_scraper_draft.get('commit_message') or None
    draft_code = session_scraper_draft.get('code')
    #draft_tags = session_scraper_draft.get('commaseparatedtags', '')

    save_code(draft_scraper, request.user, draft_code, True)


    # work out where to send them next
    #go to the scraper page if commited, or the editor if not
    if action == 'save':
        response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})
    elif action == 'commit':
        response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})

    return HttpResponseRedirect(response_url)

# called from the edit function
def saveeditedscraper(request, lscraper):
    form = forms.editorForm(request.POST, instance=lscraper)

    #validate
    if not form.is_valid() or 'action' not in request.POST:
        return HttpResponse(json.dumps({'status' : 'Failed'}))

    action = request.POST.get('action').lower()

    # recover the altered object from the form, without saving it to django database - http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method
    scraper = form.save(commit=False)
    if not scraper.guid:
        scraper.buildfromfirsttitle()

    # Add some more fields to the form
    code = form.cleaned_data['code']
    #!scraper.description = form.cleaned_data['description']    
    #!scraper.license = form.cleaned_data['license']
    #!scraper.run_interval = form.cleaned_data['run_interval']

    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        #!commitmessage = action.startswith('commit') and request.POST.get('commit_message', "changed") or None
        save_code(scraper, request.user, code, False)  # though not always not new

        # Work out the URL to return in the JSON object
        url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name':scraper.short_name})
        if action.startswith("commit"):
            #!url = reverse('scraper_code', kwargs={'wiki_type': scraper.wiki_type, 'scraper_short_name':scraper.short_name})
            response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})

        # Build the JSON object and return it
        res = json.dumps({'redirect':'true', 'url':response_url,})
        return HttpResponse(res)

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'commaseparatedtags': request.POST.get('commaseparatedtags'), 'commit_message': request.POST.get('commit_message')}
        request.session['ScraperDraft'] = draft_session_scraper

        # Set a message with django_notify telling the user their scraper is safe
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        scraper.action = action

        status = 'Failed'
        response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})
        if action == 'save':
            status = 'OK'
        elif action == 'commit':
            #!response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
            status = 'OK'

        return HttpResponse(json.dumps({'status':status, 'draft':'True', 'url':response_url}))


#Editor form
def edit(request, short_name='__new__', wiki_type='scraper', language='Python', tutorial_scraper=None):

    #return url (where to exit the editor to)
    return_url = reverse('frontpage')

    # identify the scraper (including if there was a draft one backed up)
    has_draft = False
    if request.session.get('ScraperDraft', None):
        draft = request.session['ScraperDraft'].get('scraper', None)
        if draft:
            has_draft  = True

    commit_message = ''
    if has_draft:
        scraper = draft
        commaseparatedtags = request.session['ScraperDraft'].get('commaseparatedtags', '')
        commit_message = request.session['ScraperDraft'].get('commit_message', '')        
        code = request.session['ScraperDraft'].get('code', ' missing')

    # Try and load an existing scraper
    elif short_name is not "__new__":
        scraper = get_object_or_404(models.Code, short_name=short_name)
        code = scraper.saved_code()
        if scraper.wiki_type == 'scraper':
            return_url = reverse('scraper_overview', kwargs={'scraper_short_name': scraper.short_name})
        else:
            return_url = reverse('view_overview', kwargs={'short_name': scraper.short_name})
        #!commaseparatedtags = ", ".join([tag.name for tag in scraper.tags])
        if not scraper.published:
            commit_message = 'Scraper created'

    # Create a new scraper
    else:
        if language not in ['Python', 'PHP', 'Ruby']:
            language = 'Python'

        scraper = None
        if wiki_type == 'scraper':
            scraper = models.Scraper()
        elif  wiki_type == 'view':
            scraper = models.View()
        else:
            raise Exception, "Invalid wiki type"

        startupcode = "# blank"

        if tutorial_scraper:
            startup_scraper = get_object_or_404(models.Code, short_name=tutorial_scraper)
            startupcode = startup_scraper.saved_code()
            language = startup_scraper.language
        else:
            if request.GET.get('template', False):
                startup_scrapers = models.Code.objects.filter(published=True, isstartup=True, language=language, short_name=request.GET.get('template', False))
                if len(startup_scrapers):
                    startupcode = startup_scrapers[random.randint(0, len(startup_scrapers)-1)].saved_code()

        scraper.language = language
        code = startupcode
        commaseparatedtags = ''

    # if it's a post-back (save) then execute that
    if request.POST:
        return saveeditedscraper(request, scraper)
    else:
        # Else build the page
        form = forms.editorForm(instance=scraper)
        form.fields['code'].initial = code
        #form.fields['commaseparatedtags'].initial = commaseparatedtags 

        tutorial_scrapers = models.Code.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')

    context = {}
    context['form'] = form
    context['tutorial_scrapers'] = models.Code.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')
    context['scraper'] = scraper
    context['has_draft'] = has_draft
    context['user'] = request.user
    context['docs'] = 'frontend/inline_code_docs_%s.html' % scraper.language.lower()

    return render_to_response('editor/editor.html', context, context_instance=RequestContext(request))
