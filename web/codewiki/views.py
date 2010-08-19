from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from django.contrib.auth.models import User

from django.conf import settings

from codewiki import models
from codewiki import forms
from codewiki.forms import ChooseTemplateForm
import vc

import frontend

import subprocess

import StringIO, csv, types
import datetime
from django.utils.encoding import smart_str

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

    return render_to_response('codewiki/admin.html', {
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


def stringnot(v):
    """
    (also from scraperwiki/web/api/emitters.py CSVEmitter render()
    as below -- not sure what smart_str needed for)
    """
    if v == None:
        return ""
    if type(v) == float:
        return v
    if type(v) == int:
        return v
    return smart_str(v)


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

    keyset = set()
    for row in dictlist:
        if "latlng" in row:   # split the latlng
            row["lat"], row["lng"] = row.pop("latlng")
        row.pop("date_scraped")
        keyset.update(row.keys())
    allkeys = sorted(keyset)

    fout = StringIO.StringIO()
    writer = csv.writer(fout, dialect='excel')
    writer.writerow(allkeys)
    for rowdict in dictlist:
        writer.writerow([stringnot(rowdict.get(key))  for key in allkeys])

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=%s.csv' % (scraper_short_name)
    response.write(fout.getvalue())

    return response
    #template = loader.get_template('codewiki/data.csv')
    #context = Context({'data_tables': data_tables,})


def scraper_table(request):
    dictionary = { }
    dictionary["scrapers"] = models.Scraper.objects.filter(published=True).order_by('-created_at')
    dictionary["loggedinusers"] = set([ userscraperediting.user  for usercodeediting in models.UserCodeEditing.objects.filter(user__isnull=False)])
    dictionary["numloggedoutusers"] = len(models.UserCodeEditing.objects.filter(user__isnull=True))
    dictionary["numdraftscrapersediting"] = len(models.UserCodeEditing.objects.filter(scraper__isnull=True))
    dictionary["numunpublishedscrapersediting"] = len(models.UserCodeEditing.objects.filter(scraper__published=True))
    dictionary["numpublishedscrapersediting"] = len(models.UserCodeEditing.objects.filter(scraper__published=False))
    dictionary["numpublishedscraperstotal"] = len(dictionary["scrapers"])
    dictionary["numunpublishedscraperstotal"] = len(models.Scraper.objects.filter(published=False))
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
    # uses a GET due to agent.request in twister not knowing how to use POST and send stuff
    if 'value' not in request.GET:
        return HttpResponse("needs value=")
    tstatus = json.loads(request.GET.get('value'))
    
    twisterclientnumbers = set()  # used to delete the ones that no longer exist
    
    # we are making objects in django to represent the objects in twister for editor windows open
    for client in tstatus["clientlist"]:
        # fixed attributes of the object
        twisterclientnumber = client["clientnumber"]
        twisterclientnumbers.add(twisterclientnumber)
        try:
            user = client['username'] and models.User.objects.get(username=client['username']) or None
            scraper = client['guid'] and models.Scraper.objects.get(guid=client['guid']) or None
        except:
            continue
        
        # identify or create the editing object
        lusercodeediting= models.UserCodeEditing.objects.filter(twisterclientnumber=twisterclientnumber)
        if not luserscraperediting:
            usercodeediting= models.UserCodeEditing(user=user, scraper=scraper, twisterclientnumber=twisterclientnumber)
            userscraperediting.editingsince = datetime.datetime.now()
        else:
            # this assertion is firing and sending us emails.  please investigate to find out how 
            # extra copies of the UserCodeEditing objects are getting created?  
            # This may be because there are two threads getting into this function simultaneously 
            # from twister callbacks.  If this is verified as the case (and not some other avoidable bug), then it's 
            # okay to delete the superfluous one, as long as this doesn't cause any problems (eg the other thread might be doing this at the same time)
            assert len(luserscraperediting) == 1, [luserscraperediting]  
            
            usercodeediting= luserscraperediting[0]
            assert userscraperediting.user == user, ("different", userscraperediting.user, user)
            assert userscraperediting.scraper == scraper, ("different", userscraperediting.scraper, scraper)
        
        # updateable values of the object
        userscraperediting.twisterscraperpriority = client['scrapereditornumber']

        # this condition could instead reference a running object
        if client['running'] and not userscraperediting.runningsince:
            userscraperediting.runningsince = datetime.datetime.now()
        if not client['running'] and userscraperediting.runningsince:
            userscraperediting.runningsince = None
        
        userscraperediting.save()

    # discard now closed values of the object
    for usercodeediting in models.UserCodeEditing.objects.all():
        if userscraperediting.twisterclientnumber not in twisterclientnumbers:
            userscraperediting.delete()
            # or could use the field: closedsince  = models.DateTimeField(blank=True, null=True)
    return HttpResponse("Howdy ppp ")

def rpcexecute_dummy(request, scraper_short_name):
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
def rpcexecute(request, scraper_short_name):
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