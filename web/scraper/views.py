from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from django.conf import settings

from scraper import models
from scraper import forms
from scraper.forms import SearchForm
import frontend

import StringIO, csv
from django.utils.encoding import smart_str

try:
    import json
except ImportError:
    import simplejson as json

def overview(request, scraper_short_name):
    """
    Shows info on the scraper plus example data.

    This is the main scraper view (default tab)
    """
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects,
        short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_tags = Tag.objects.get_for_object(scraper)

    table = models.Scraper.objects.data_summary(
        scraper_id=scraper.guid,
        limit=1)
    data = None
    has_data = len(table['rows']) > 0
    if has_data:
        data = zip(table['headings'], table['rows'][0])

    return render_to_response('scraper/overview.html', {
        'scraper_tags': scraper_tags,
        'selected_tab': 'overview',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        'has_data': has_data,
        'data': data,
        }, context_instance=RequestContext(request))


def create(request):
    """
    Rendars the scraper create form

    Is this unused?

    TODO: delete!
    """
    if request.method == 'POST':
        return render_to_response(
            'scraper/create.html',
            context_instance=RequestContext(request))
    else:
        return render_to_response(
            'scraper/create.html',
            context_instance=RequestContext(request))


def scraper_data(request, scraper_short_name):
    #user details
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    #if user has requested a delete, **double** check they are allowed to,
    # the do the delete
    if request.method == 'POST':
        delete_data = request.POST['delete_data']
        if delete_data == '1' and user_owns_it:
            models.Scraper.objects.clear_datastore(
                scraper_id=scraper.guid)

    #get data for this scaper
    data = models.Scraper.objects.data_summary(
                            scraper_id=scraper.guid, limit=500)

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


def scraper_map(request, scraper_short_name):

    #user details
    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    scraper_tags = Tag.objects.get_for_object(scraper)

    #get data for this scaper
    data = models.Scraper.objects.data_summary(
        scraper_id=scraper.guid, limit=250)
    has_data = len(data['rows']) > 0
    data = json.dumps(data)

    return render_to_response('scraper/map.html', {
    'scraper_tags': scraper_tags,
    'selected_tab': 'map',
    'scraper': scraper,
    'user_owns_it': user_owns_it,
    'user_follows_it': user_follows_it,
    'data': data,
    'has_data': has_data,
    'has_map': True,
    }, context_instance=RequestContext(request))


def code(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    committed_code = scraper.committed_code()
    scraper_tags = Tag.objects.get_for_object(scraper)

    return render_to_response('scraper/code.html', {
        'scraper_tags': scraper_tags,
        'selected_tab': 'code',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'committed_code': committed_code,
        'user_follows_it': user_follows_it,},
        context_instance=RequestContext(request))


def contributors(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()

    scraper_tags = Tag.objects.get_for_object(scraper)

    return render_to_response('scraper/contributers.html', {
        'scraper_tags': scraper_tags,
        'scraper_owner': scraper_owner,
        'scraper_contributors': scraper_contributors,
        'scraper_followers': scraper_followers,
        'selected_tab': 'contributors',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        }, context_instance=RequestContext(request))


def comments(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects, short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())

    scraper_owner = scraper.owner()
    scraper_contributors = scraper.contributors()
    scraper_followers = scraper.followers()

    scraper_tags = Tag.objects.get_for_object(scraper)

    return render_to_response('scraper/comments.html', {
        'scraper_tags': scraper_tags,
        'scraper_owner': scraper_owner,
        'scraper_contributors': scraper_contributors,
        'scraper_followers': scraper_followers,
        'selected_tab': 'comments',
        'scraper': scraper,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        }, context_instance=RequestContext(request))


def scraper_history(request, scraper_short_name):

    user = request.user
    scraper = get_object_or_404(
        models.Scraper.objects,
        short_name=scraper_short_name)
    user_owns_it = (scraper.owner() == user)
    user_follows_it = (user in scraper.followers())
    content_type = scraper.content_type()
    history = frontend.models.Alerts.objects.filter(
        content_type=content_type,
        object_id=scraper.pk).order_by('-datetime')

    return render_to_response('scraper/history.html', {
        'selected_tab': 'history',
        'scraper': scraper,
        'history': history,
        'user_owns_it': user_owns_it,
        'user_follows_it': user_follows_it,
        }, context_instance=RequestContext(request))


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
    #template = loader.get_template('scraper/data.csv')
    #context = Context({'data_tables': data_tables,})


def scraper_list(request):
    #scrapers =
    #   models.Scraper.objects.filter(published=True).order_by('-created_at')

    # return render_to_response('scraper/list.html', {'scrapers': scrapers},
    # context_instance = RequestContext(request))

    all_scrapers = models.Scraper.objects.filter(
        published=True).order_by('-created_at')

    # Number of results to show from settings
    paginator = Paginator(
        all_scrapers,
        settings.SCRAPERS_PER_PAGE)

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

    return render_to_response(
        'scraper/list.html',
        {
            "scrapers": scrapers,
            "form": form,},
            context_instance=RequestContext(request))


def download(request, scraper_short_name):
    """
    TODO: DELETE?
    """
    scraper = get_object_or_404(models.Scraper.objects, 
                                short_name=scraper_short_name)
    response = HttpResponse(scraper.committed_code(), mimetype="text/plain")
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
            return HttpResponseRedirect('/scrapers/search/%s/' % q)
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
