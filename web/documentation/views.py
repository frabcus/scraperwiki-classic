from django.template import RequestContext
from django.shortcuts import render_to_response

def catchall(request, path=None):
    lang = request.GET.get('lang', None) or request.session.get('lang', 'python')
    request.session['lang'] = lang
    
    if path:
        template = 'documentation/%s.html' % path
    else:
        template = 'documentation/index.html'

    return render_to_response(template, {'lang': lang}, context_instance=RequestContext(request))
