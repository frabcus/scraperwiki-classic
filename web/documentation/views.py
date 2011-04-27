from django.template import RequestContext, TemplateDoesNotExist
from django.shortcuts import render_to_response
from django.http import Http404
import re
import codewiki

def docmain(request, path=None):
    language = request.GET.get('language', None) or request.session.get('language', 'python')
    request.session['language'] = language
    context = {'language':language }
    context["title"] = path
    if path:
        context["docpage"] = 'documentation/includes/%s' % re.sub("\.\.", "", path)  # remove attempts to climb into another directory
    
    try:
        return render_to_response('documentation/docbase.html', context, context_instance=RequestContext(request))
    except TemplateDoesNotExist:
        raise Http404


    # should also filter, say, on isstartup=True and on privacy_status=visible to limit what can be injected into here
def contrib(request, short_name):
    context = { }
    try:
        scraper = codewiki.models.Code.objects.filter(language="html").get(short_name=short_name) 
    except models.Code.DoesNotExist:
        raise Http404
    if not scraper.actionauthorized(request.user, "readcode"):
        raise Http404
    
    context["doccontents"] = scraper.get_vcs_status(-1)["code"]
    context["title"] = scraper.title
    context["scraper"] = scraper
    return render_to_response('documentation/docbase.html', context, context_instance=RequestContext(request))
