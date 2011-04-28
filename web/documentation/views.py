from django.template import RequestContext, TemplateDoesNotExist
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseNotFound
from codewiki.models import Code
import os
import re
import codewiki
import settings
import urllib2


def docmain(request, language=None, path=None):
    from titles import page_titles
    
#    language = request.GET.get('language', None) or request.session.get('language', 'python')
    if language is None:
        language = request.session.get('language', 'python')
    request.session['language'] = language
    context = {'language':language }
    
    if path:
        title, para = page_titles[path]
        context["title"] = title
        context["para"] = para
        
        # Maybe we should render a template instead for now?
        context["docpage"] = 'documentation/includes/%s.html' % re.sub("\.\.", "", path)  # remove attempts to climb into another directory
        if not os.path.exists(os.path.join(settings.SCRAPERWIKI_DIR, "templates", context["docpage"])):
            raise Http404
            
    return render_to_response('documentation/docbase.html', context, context_instance=RequestContext(request))



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
    api_base = "http://%s/api/1.0/" % settings.API_DOMAIN
    return render_to_response('documentation/apibase.html', {"api_base":api_base}, context_instance=RequestContext(request))

def api_explorer(request):
    styout = '<pre style="background:#000; color:#fff;">%s</pre>'  # can't be done by formatting the iframe
    if not request.POST:
        return HttpResponse(styout % "Select a function, add values above, then click 'call method'\nto see live data")
    url = request.POST.get("apiurl")
    api_base = "http://%s/api/1.0/" % settings.API_DOMAIN
    assert url[:len(api_base)] == api_base
    result = urllib2.urlopen(url).read()
    return HttpResponse(styout % re.sub("<", "&lt;", result))



