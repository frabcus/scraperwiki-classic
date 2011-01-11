from django.contrib.sites.models import Site
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.management import call_command
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.decorators.http import condition
import textile
import random
from django.conf import settings
from django.utils.encoding import smart_str

from codewiki import models
from api.emitters import CSVEmitter 
import vc
import frontend

import difflib
import re
import csv
import math
import urllib2
import base64

from cStringIO import StringIO
import csv, types
import datetime
import gdata.docs.service


try:                import json
except ImportError: import simplejson as json

# kick this function out to the model module so it can be used elsewhere
def get_code_object(short_name, request):
    lcodeobject = models.Code.unfiltered.filter(short_name=short_name)
    assert len(lcodeobject) <= 1
    if len(lcodeobject) == 0:
        return HttpResponseNotFound(render_to_string('404.html', {'heading': 'Not found', 'body': "Sorry, this scraper does not exist"}, context_instance=RequestContext(request)))
    codeobject = lcodeobject[0]
    if codeobject.deleted:
        return HttpResponseNotFound(render_to_string('404.html', {'heading': 'Deleted', 'body': "Sorry, this scraper has been deleted by its owner"}, context_instance=RequestContext(request)))
    if not codeobject.published and not request.user.is_authenticated():
        return HttpResponseNotFound(render_to_string('404.html', {'heading': 'Access denied', 'body': "Sorry, this scraper is not public"}, context_instance=RequestContext(request)))
    return codeobject


# preview of the code diffed
def code(request, wiki_type, short_name):
    scraper = get_code_object(short_name, request)
    if isinstance(scraper, HttpResponseNotFound):
        return scraper

    try: rev = int(request.GET.get('rev', '-1'))
    except ValueError: rev = -1

    mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
    status = mercurialinterface.getstatus(scraper, rev)

    context = { 'selected_tab': 'history', 'scraper': scraper }

    # overcome lack of subtract in template
    if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
        status["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]

    context["status"] = status
    context["code"] = status.get('code')
    
    # hack in link to user (was it a good idea to use userid rather than username?)
    try:    status["currcommit"]["user"] = User.objects.get(pk=int(status["currcommit"]["userid"]))
    except: pass
    try:    status["prevcommit"]["user"] = User.objects.get(pk=int(status["prevcommit"]["userid"]))
    except: pass
    try:    status["nextcommit"]["user"] = User.objects.get(pk=int(status["nextcommit"]["userid"]))
    except: pass

    context['error_messages'] = [ ]
    
    try: otherrev = int(request.GET.get('otherrev', '-1'))
    except ValueError: otherrev = None
    
    if otherrev != -1:
        try:
            reversion = mercurialinterface.getreversion(otherrev)
            context["othercode"] = reversion["text"].get(status['scraperfile'])
        except IndexError:
            context['error_messages'].append('Bad otherrev index')

    if context.get("othercode"):
        sqm = difflib.SequenceMatcher(None, context["code"].splitlines(), context["othercode"].splitlines())
        context['matcheropcodes'] = json.dumps(sqm.get_opcodes())
    
    return render_to_response('codewiki/code.html', context, context_instance=RequestContext(request))


  # combine these two
def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if not code:
        return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')

    scraper = get_code_object(short_name, request)
    if isinstance(scraper, HttpResponseNotFound):
        return scraper

    result = '\n'.join(difflib.unified_diff(scraper.saved_code().splitlines(), code.splitlines(), lineterm=''))
    return HttpResponse("::::" + result, mimetype='text')


  # obviously did not know about json technology here
def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')

    scraper = get_code_object(short_name, request)
    if isinstance(scraper, HttpResponseNotFound):
        return scraper

    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        result = "%s:::sElEcT rAnGe:::%s" % (json.dumps(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        result = newcode
    return HttpResponse(result, mimetype="text/plain")

  
  # try to get rid of this
def edittutorial(request, short_name):
    code = get_code_object(short_name, request)
    if isinstance(code, HttpResponseNotFound):
        return scraper

    qtemplate = "?template="+code.short_name
    return HttpResponseRedirect(reverse('editor', args=[code.wiki_type, code.language]) + qtemplate)




blankstartupcode = { 'scraper' : { 'python': "# Blank Python\n", 
                                    'php':   "<?php\n# Blank PHP\n?>\n", 
                                    'ruby':  "# Blank Ruby\n" 
                                 }, 
                     'view'    : { 'python': "# Blank Python\nsourcescraper = ''\n", 
                                   'php':    "<?php\n# Blank PHP\n$sourcescraper = ''\n?>\n", 
                                   'ruby':   "# Blank Ruby\nsourcescraper = ''\n" 
                                  }
                   }


def edit(request, short_name='__new__', wiki_type='scraper', language='python'):
    language = language.lower()
    
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
        scraper = get_code_object(short_name, request)
        if isinstance(scraper, HttpResponseNotFound):
            return scraper
        status = vc.MercurialInterface(scraper.get_repo_path()).getstatus(scraper, -1)
        assert 'currcommit' not in status and not status['ismodified']
        context['code'] = status["code"]
        context['rev'] = status['prevcommit']

    # create a temporary scraper object
    else:
        if wiki_type == 'view':
            scraper = models.View()
        else:
            scraper = models.Scraper()

        statuptemplate = request.GET.get('template')
        if statuptemplate:
            try:
                templatescraper = models.Code.objects.get(published=True, language=language, short_name=statuptemplate)
                startupcode = templatescraper.saved_code()
            except models.Code.DoesNotExist:
                startupcode = startupcode.replace("Blank", "Missing template for")
        else:
            startupcode = blankstartupcode[wiki_type][language]
            
        # replace the phrase: sourcescraper = 'working-example' with sourcescraper = 'replacement-name'
        inputscrapername = request.GET.get('sourcescraper', False)
        if inputscrapername:
            startupcode = re.sub('''(?<=sourcescraper = ["']).*?(?=["'])''', inputscrapername, startupcode)
        
        scraper.language = language
        context['code'] = startupcode

    #if a source scraper has been set, then pass it to the page
    if scraper.wiki_type == 'view' and request.GET.get('sourcescraper'):
        context['source_scraper'] = request.GET.get('sourcescraper')

    context['scraper']          = scraper
    context['quick_help_template'] = 'codewiki/includes/%s_quick_help_%s.html' % (scraper.wiki_type, scraper.language.lower())
    
    return render_to_response('codewiki/editor.html', context, context_instance=RequestContext(request))



#save a code object (source scraper is to make thin link from the view to the scraper
def save_code(code_object, user, code_text, earliesteditor, commitmessage, sourcescraper = ''):

    code_object.line_count = int(code_text.count("\n"))
    if code_object.published and code_object.first_published_at == None:
        code_object.first_published_at = datetime.datetime.today()
    
    # work around the botched code/views/scraper inheretance.  
    # if publishing for the first time set the first published date
    
    if code_object.wiki_type == "scraper":
        code_object.save()  # save the object using the base class (otherwise causes a major failure if it doesn't exist)
        code_object.scraper.update_meta()  # would be ideal to in-line this (and render it's functionality defunct as the data is about the database, not the scraper)
        code_object.scraper.save()
    else:
        code_object.save()

        #make link to source scraper
        if sourcescraper:
            lsourcescraper = models.Code.objects.filter(short_name=sourcescraper)
            if lsourcescraper:
                code_object.relations.add(lsourcescraper[0])

    # save code and commit code through the mercurialinterface
    mercurialinterface = vc.MercurialInterface(code_object.get_repo_path())
    mercurialinterface.savecode(code_object, code_text)  # creates directory 
    lcommitmessage = earliesteditor and ("%s|||%s" % (earliesteditor, commitmessage)) or commitmessage
    rev = mercurialinterface.commit(code_object, message=lcommitmessage, user=user)

    # Add user roles
    if code_object.owner():
        if code_object.owner().pk != user.pk:
            code_object.add_user_role(user, 'editor')
    else:
        code_object.add_user_role(user, 'owner')
    
    return rev # None if no change


# called from the edit function
def handle_editor_save(request):
    guid = request.POST.get('guid', '')
    title = request.POST.get('title', '')
    language = request.POST.get('language', '').lower()
    
    if not title or title.lower() == 'untitled':
        return HttpResponse(json.dumps({'status' : 'Failed', 'message':"title is blank or untitled"}))
    
    if guid:
        scraper = models.Code.objects.get(guid=guid)
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
        scraper.buildfromfirsttitle()
            
    code = request.POST.get('code', "")
    sourcescraper = request.POST.get('sourcescraper', "")
    commitmessage = request.POST.get('commit_message', "")
    
    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        earliesteditor = request.POST.get('earliesteditor', "")
        rev = save_code(scraper, request.user, code, earliesteditor, commitmessage, sourcescraper)  
        response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})
        return HttpResponse(json.dumps({'redirect':'true', 'url':response_url, 'rev':rev }))

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'sourcescraper': sourcescraper }
        request.session['ScraperDraft'] = draft_session_scraper

        # Set a message with django_notify telling the user their scraper is safe
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})
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
    save_code(draft_scraper, request.user, draft_code, earliesteditor, commitmessage, sourcescraper)

    response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})
    return HttpResponseRedirect(response_url)


