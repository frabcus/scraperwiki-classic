from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings

from codewiki import models

import vc
import difflib
import re
import urllib
import os
from codewiki.management.commands.run_scrapers import GetDispatcherStatus

try:                 import json
except ImportError:  import simplejson as json


def getscraperor404(request, short_name, action):
    try:
        scraper = models.Code.unfiltered.get(short_name=short_name)
    except models.Code.DoesNotExist:
        raise Http404
    if not scraper.actionauthorized(request.user, action):
        raise Http404
    return scraper

        
def raw(request, short_name):  # this is used by swimport
    scraper = getscraperor404(request, short_name, "readcode")
    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1
    code = scraper.get_vcs_status(rev)["code"]
    return HttpResponse(code, mimetype="text/plain")


def diffseq(request, short_name):
    scraper = getscraperor404(request, short_name, "readcode")
    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1
    try: otherrev = int(request.GET.get('otherrev', '-1'))
    except ValueError: otherrev = None

    code = scraper.get_vcs_status(rev)["code"]
    othercode = scraper.get_vcs_status(otherrev)["code"]

    sqm = difflib.SequenceMatcher(None, code.splitlines(), othercode.splitlines())
    result = sqm.get_opcodes()  # [ ("replace|delete|insert|equal", i1, i2, j1, j2) ]
    return HttpResponse(json.dumps(result))


# NB: It only accepts the run_id hashes (NOT the Django id) so people can't
# run through every value and get the URL names of each scraper.
def run_event_json(request, run_id):
    try:
        event = models.ScraperRunEvent.objects.get(run_id=run_id)
    except models.ScraperRunEvent.DoesNotExist:
        raise Http404
    if not event.scraper.actionauthorized(request.user, "readcode"):
        raise Http404
    
    result = { 'records_produced':event.records_produced, 'pages_scraped':event.pages_scraped, "output":event.output, 
               'first_url_scraped':event.first_url_scraped, 'exception_message':event.exception_message }
    if event.run_started:
        result['run_started'] = event.run_started.isoformat()
    if event.run_ended:
        result['run_ended'] = event.run_ended.isoformat()
    
    statusscrapers = GetDispatcherStatus()
    for status in statusscrapers:
        if status['runID'] == event.run_id:
            result['dispatcherstatus'] = status
    
    return HttpResponse(json.dumps(result))



def reload(request, short_name):
    scraper = getscraperor404(request, short_name, "readcode")
    oldcodeineditor = request.POST.get('oldcode')
    status = scraper.get_vcs_status(-1)
    result = { "code": status["code"], "rev":status.get('prevcommit',{}).get('rev') }
    if oldcodeineditor:
        result["selrange"] = vc.DiffLineSequenceChanges(oldcodeineditor, status["code"])
    return HttpResponse(json.dumps(result))




blankstartupcode = { 'scraper' : { 'python': "# Blank Python\n", 
                                    'php':   "<?php\n# Blank PHP\n?>\n", 
                                    'ruby':  "# Blank Ruby\n",
                                 }, 
                     'view'    : { 'python': "# Blank Python\nsourcescraper = ''\n", 
                                   'php':    "<?php\n# Blank PHP\n$sourcescraper = ''\n?>\n", 
                                   'ruby':   "# Blank Ruby\nsourcescraper = ''\n",
                                   'html':   "<p>Blank HTML page</p>\n",
                                   'javascript':"// Blank javascript\n",
                                  }
                   }

def edit(request, short_name='__new__', wiki_type='scraper', language='python'):
    
        # quick and dirty corrections to incoming urls, which should really be filtered in the url.py settings
    language = language.lower()
    if language not in blankstartupcode[wiki_type]:
        language = 'python'
    
    context = {'selected_tab':'code'}
    
    if re.match('[\d\.\w]+$', request.GET.get('codemirrorversion', '')):
        context["codemirrorversion"] = request.GET.get('codemirrorversion')
    else:
        context["codemirrorversion"] = settings.CODEMIRROR_VERSION

    # if this is a matching draft scraper pull it in
    draftscraper = request.session.get('ScraperDraft')
    if draftscraper and draftscraper.get('scraper') and (short_name == "__new__" or draftscraper.get('scraper').short_name == short_name):
        scraper = draftscraper.get('scraper')
        context['code'] = draftscraper.get('code', ' missing')
        context['rev'] = 'draft'
    
    # Load an existing scraper preference
    elif short_name != "__new__":
        try:
            scraper = models.Code.unfiltered.get(short_name=short_name)
        except models.Code.DoesNotExist:
            message =  "Sorry, this %s does not exist" % wiki_type
            return HttpResponseNotFound(render_to_string('404.html', {'heading':'Not found', 'body':message}, context_instance=RequestContext(request)))
        if wiki_type != scraper.wiki_type:
            return HttpResponseRedirect(reverse("editor_edit", args=[scraper.wiki_type, short_name]))
        if not scraper.actionauthorized(request.user, "readcodeineditor"):
            return HttpResponseNotFound(render_to_string('404.html', scraper.authorizationfailedmessage(request.user, "readcodeineditor"), context_instance=RequestContext(request)))
        
        
        status = scraper.get_vcs_status(-1)
        assert 'currcommit' not in status 
        # assert not status['ismodified']  # should hold, but disabling it for now
        context['code'] = status["code"]
        context['rev'] = status['prevcommit']

    # create a temporary scraper object
    else:
        if wiki_type == 'view':
            scraper = models.View()
        else:
            scraper = models.Scraper()

        startupcode = blankstartupcode[wiki_type][language]

        statuptemplate = request.GET.get('template') or request.GET.get('fork')
        if statuptemplate:
            try:
                templatescraper = models.Code.unfiltered.get(short_name=statuptemplate)
                if not templatescraper.actionauthorized(request.user, "readcode"):
                    startupcode = startupcode.replace("Blank", "Not authorized to read this code")
                else:
                    startupcode = templatescraper.saved_code()
                    if 'fork' in request.GET:
                        scraper.title = templatescraper.title
            except models.Code.DoesNotExist:
                startupcode = startupcode.replace("Blank", "Missing template for")
            
        # replace the phrase: sourcescraper = 'working-example' with sourcescraper = 'replacement-name'
        inputscrapername = request.GET.get('sourcescraper', False)
        if inputscrapername:
            startupcode = re.sub('''(?<=sourcescraper = ["']).*?(?=["'])''', inputscrapername, startupcode)
        
        scraper.language = language
        context['code'] = startupcode

    #if a source scraper has been set, then pass it to the page
    if scraper.wiki_type == 'view' and request.GET.get('sourcescraper'):
        context['source_scraper'] = request.GET.get('sourcescraper')

    #if a fork scraper has been set, then pass it to the page
    if request.GET.get('fork'):
        context['fork'] = request.GET.get('fork')

    context['scraper'] = scraper
    context['quick_help_template'] = 'codewiki/includes/%s_quick_help_%s.html' % (scraper.wiki_type, scraper.language.lower())
    
    return render_to_response('codewiki/editor.html', context, context_instance=RequestContext(request))



    # save a code object (source scraper is to make thin link from the view to the scraper
    # this is called in two places, due to those draft scrapers saved in the session
    # would be better if the saving was deferred and not done right following a sign in
def save_code(code_object, user, code_text, earliesteditor, commitmessage, sourcescraper=''):
    assert code_object.actionauthorized(user, "savecode")
    code_object.line_count = int(code_text.count("\n"))
    
    # work around the botched code/views/scraper inheretance.  
    # if publishing for the first time set the first published date
    
    code_object.save()  # save the object using the base class (otherwise causes a major failure if it doesn't exist)
    commit_message = earliesteditor and ("%s|||%s" % (earliesteditor, commitmessage)) or commitmessage
    rev = code_object.commit_code(code_text, commit_message, user)

    if code_object.wiki_type == "scraper":
        try:
            code_object.scraper.update_meta()  # would be ideal to in-line this (and render it's functionality defunct as the data is about the database, not the scraper)
        except:
            pass
        code_object.scraper.save()
    else:
        #make link to source scraper
        if sourcescraper:
            lsourcescraper = models.Code.objects.filter(short_name=sourcescraper)
            if lsourcescraper:
                code_object.relations.add(lsourcescraper[0])

    # Add user roles
    if code_object.owner():
        if code_object.owner().pk != user.pk:
            code_object.add_user_role(user, 'editor')
    else:
        code_object.add_user_role(user, 'owner')
    
    return rev # None if no change


    # called from the editor
def handle_editor_save(request):
    guid = request.POST.get('guid', '')
    title = request.POST.get('title', '')
    language = request.POST.get('language', '').lower()
    
    if not title or title.lower() == 'untitled':
        return HttpResponse(json.dumps({'status' : 'Failed', 'message':"title is blank or untitled"}))
    
    if guid:
        try:
            scraper = models.Code.unfiltered.get(guid=guid)   # should this use short_name?
        except models.Code.DoesNotExist:
            return HttpResponse(json.dumps({'status' : 'Failed', 'message':"Name or guid invalid"}))
        
        assert scraper.language.lower() == language
        assert scraper.wiki_type == request.POST.get('wiki_type', '')
        scraper.title = title   # the save is done on save_code
        
    else:
        if request.POST.get('wiki_type') == 'view':
            scraper = models.View()
        else:
            scraper = models.Scraper()
        scraper.language = language
        scraper.title = title

        fork = request.POST.get("fork", None)
        if fork:
            try:
                scraper.forked_from = models.Code.objects.get(short_name=fork)
            except models.Code.DoesNotExist:
                pass
            
    code = request.POST.get('code', "")
    sourcescraper = request.POST.get('sourcescraper', "")
    commitmessage = request.POST.get('commit_message', "")
    
    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        earliesteditor = request.POST.get('earliesteditor', "")
        if not scraper.actionauthorized(request.user, "savecode"):
            return HttpResponse(json.dumps({'status':'Failed', 'message':"Not allowed to save this scraper"}))
        rev = save_code(scraper, request.user, code, earliesteditor, commitmessage, sourcescraper)  
        response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})
        return HttpResponse(json.dumps({'redirect':'true', 'url':response_url, 'rev':rev }))

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'sourcescraper': sourcescraper }
        request.session['ScraperDraft'] = draft_session_scraper

        # Set a message with django_notify telling the user their scraper is safe
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        response_url = reverse('editor', kwargs={'wiki_type': scraper.wiki_type, 'language': scraper.language.lower()})
        return HttpResponse(json.dumps({'status':'OK', 'draft':'True', 'url':response_url}))


# retrieves draft scraper, saves and goes to the editor page
def handle_session_draft(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login') + "?next=%s" % reverse('handle_session_draft'))

    session_scraper_draft = request.session.pop('ScraperDraft', None)
    if not session_scraper_draft:  # shouldn't be here
        return HttpResponseRedirect(reverse('frontpage'))

    draft_scraper = session_scraper_draft.get('scraper', None)
    draft_scraper.save()
    draft_code = session_scraper_draft.get('code')
    sourcescraper = session_scraper_draft.get('sourcescraper')
    commitmessage = session_scraper_draft.get('commit_message', "") # needed?
    earliesteditor = session_scraper_draft.get('earliesteditor', "") #needed?
        
        # we reload into editor but only save for an authorized user
    if draft_scraper.actionauthorized(request.user, "savecode"):
        save_code(draft_scraper, request.user, draft_code, earliesteditor, commitmessage, sourcescraper)

    response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})
    return HttpResponseRedirect(response_url)



        # this definitely should be ported into javascript so it can respond to selections
def getselectedword(line, character, language):
    try: 
        ip = int(character)
    except ValueError:
        return None
    ie = ip
    while ip >= 1 and re.match("[\w\.#]", line[ip-1]):  # search left across dots
        ip -= 1
    while ie < len(line) and re.match("\w", line[ie]): # search right across characters
        ie += 1
    word = line[ip:ie]

    # search for quoted string
    while ip >= 1 and line[ip-1] not in ('"', "'"):
        ip -= 1
    while ie < len(line) and line[ie] not in ('"', "'"):
        ie += 1
    if ip >= 1 and ie < len(line) and line[ip-1] in ('"', "'") and line[ip-1] == line[ie]:
        word = line[ip:ie] 

    if re.match("\W*$", word):
        word = ""
    return word



def quickhelp(request):
    query = dict([(k, request.GET.get(k, "").encode('utf-8'))  for k in ["language", "short_name", "username", "wiki_type", "line", "character"]])
    query["word"] = getselectedword(query["line"], query["character"], query["language"])
    if re.match("http://", query["word"]):
        query["escapedurl"] = urllib.quote(query["word"])
    print query
    
    context = query.copy()
    context['quick_help_template'] = 'documentation/%s_quick_help_%s.html' % (query["wiki_type"], query["language"])
    context['query_string'] = urllib.urlencode(query)
    return render_to_response('documentation/quick_help.html', context, context_instance=RequestContext(request))



