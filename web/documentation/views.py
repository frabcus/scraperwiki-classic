from django.template import RequestContext, TemplateDoesNotExist
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from codewiki.models import Code
import os
import re
import codewiki
import settings
import urllib2


def docmain(request, language=None, path=None):
    from titles import page_titles

    language = language or request.session.get('language', 'python')
    request.session['language'] = language
    context = {'language': language }
    
    if path:
        title, para = page_titles[path]
        context["title"] = title
        context["para"] = para
        
        # Maybe we should be rendering a template from the file so that it isn't fixed 
        # as static html.
        context["docpage"] = 'documentation/includes/%s.html' % re.sub("\.\.", "", path)  # remove attempts to climb into another directory
        if not os.path.exists(os.path.join(settings.SCRAPERWIKI_DIR, "templates", context["docpage"])):
            raise Http404
    else:
        context["para"] = "Tutorials, references and guides for programmers coding on ScraperWiki"
            
    return render_to_response('documentation/docbase.html', context, context_instance=RequestContext(request))


def tutorials(request,language=None):
    from codewiki.models import Scraper, View

    if not language:
        return HttpResponseRedirect(reverse('tutorials',kwargs={'language': request.session.get('language', 'python')}) )

    tutorial_dict, viewtutorials = {}, {}
    if language == "python":
        tutorial_dict[language] = Scraper.objects.filter(privacy_status="public", istutorial=True, language=language).order_by('title')
        for scraper in tutorial_dict[language]:
            scraper.title = re.sub("^[\d ]+", "", scraper.title)
    else:
        tutorial_dict[language] = Scraper.objects.filter(privacy_status="public", istutorial=True, language=language).order_by('first_published_at')
        
    viewtutorials[language] = View.objects.filter(privacy_status="public", istutorial=True, language=language).order_by('first_published_at')
    context = {'language': language, 'tutorials': tutorial_dict, 'viewtutorials': viewtutorials}
    
    return render_to_response('documentation/tutorials.html', context, context_instance = RequestContext(request))


    # should also filter, say, on isstartup=True and on privacy_status=visible to limit what can be injected into here
def contrib(request, short_name):
    context = { }
    try:
        scraper = codewiki.models.Code.objects.filter().get(short_name=short_name) 
    except Code.DoesNotExist:
        raise Http404
    if not scraper.actionauthorized(request.user, "readcode"):
        raise Http404
    
    context["doccontents"] = scraper.get_vcs_status(-1)["code"]
    context["title"] = scraper.title

    context["scraper"] = scraper
    return render_to_response('documentation/docbase.html', context, context_instance=RequestContext(request))


def docexternal(request):
    language = request.session.get('language', 'python')
    api_base = "http://%s/api/1.0/" % settings.API_DOMAIN

    context = {'language':language, 'api_base':api_base }

    return render_to_response('documentation/apibase.html', context, context_instance=RequestContext(request))

def api_explorer(request):
    styout = '<pre style="background:#000; color:#fff;">%s</pre>'  # can't be done by formatting the iframe
    if not request.POST:
        return HttpResponse(styout % "Select a function, add values above, then click 'call method'\nto see live data")
    url = request.POST.get("apiurl")
    api_base = "http://%s/api/1.0/" % settings.API_DOMAIN
    assert url[:len(api_base)] == api_base
    result = urllib2.urlopen(url).read()
    return HttpResponse(styout % re.sub("<", "&lt;", result))



