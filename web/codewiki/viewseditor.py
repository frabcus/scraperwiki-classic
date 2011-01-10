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
from codewiki import forms
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


# duplicated function
def get_code_object_or_none(klass, short_name):
    try:
        return klass.objects.get(short_name=short_name)
    except:
        return None

# duplicated function
def code_error_response(klass, short_name, request):
    if klass.unfiltered.filter(short_name=short_name, deleted=True).count() == 1:
        body = 'Sorry, this %s has been deleted by the owner' % klass.__name__
        string = render_to_string('404.html', {'heading': 'Deleted', 'body': body}, context_instance=RequestContext(request))
        return HttpResponseNotFound(string)
    else:
        raise Http404


# preview of the code diffed
def code(request, wiki_type, short_name):
    user = request.user
    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    # Only logged in users should be able to see unpublished scrapers
    if not scraper.published and not user.is_authenticated():
        return render_to_response('codewiki/access_denied_unpublished.html', context_instance=RequestContext(request))

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


def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if not code:
        return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')

    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    result = '\n'.join(difflib.unified_diff(scraper.saved_code().splitlines(), code.splitlines(), lineterm=''))
    return HttpResponse("::::" + result, mimetype='text')

def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')

    scraper = get_code_object_or_none(models.Code, short_name=short_name)
    if not scraper:
        return code_error_response(models.Code, short_name=short_name, request=request)

    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        result = "%s:::sElEcT rAnGe:::%s" % (json.dumps(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        result = newcode
    return HttpResponse(result, mimetype="text/plain")

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
            scraper = get_code_object_or_none(models.Code, short_name=sourcescraper)
            if scraper:
                code_object.relations.add(scraper)

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
    draft_code = session_scraper_draft.get('code')
    sourcescraper = session_scraper_draft.get('sourcescraper')
    commitmessage = session_scraper_draft.get('commit_message', "") # needed?
    earliesteditor = session_scraper_draft.get('earliesteditor', "") #needed?
    save_code(draft_scraper, request.user, draft_code, earliesteditor, commitmessage, sourcescraper)

    response_url = reverse('editor_edit', kwargs={'wiki_type': draft_scraper.wiki_type, 'short_name' : draft_scraper.short_name})
    return HttpResponseRedirect(response_url)


# called from the edit function
def saveeditedscraper(request, lscraper):
    form = forms.editorForm(request.POST, instance=lscraper)
    
    #validate
    if not form.is_valid() or 'action' not in request.POST:
        return HttpResponse(json.dumps({'status' : 'Failed'}))

    action = request.POST.get('action').lower()
    # assert action == 'commit'

    # recover the altered object from the form, without saving it to django database - http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method
    scraper = form.save(commit=False)
    if not scraper.guid:
        scraper.buildfromfirsttitle()

    # Add some more fields to the form
    code = form.cleaned_data['code']
    commitmessage = request.POST.get('commit_message', "")
    sourcescraper = request.POST.get('sourcescraper', "")
    
    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        earliesteditor = request.POST.get('earliesteditor', "")
        rev = save_code(scraper, request.user, code, earliesteditor, commitmessage, sourcescraper)  

        # Work out the URL to return in the JSON object
        url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name':scraper.short_name})
        if action.startswith("commit"):
            response_url = reverse('editor_edit', kwargs={'wiki_type': scraper.wiki_type, 'short_name': scraper.short_name})

        # Build the JSON object and return it
        res = json.dumps({'redirect':'true', 'url':response_url, 'rev':rev })
        return HttpResponse(res)

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'commit_message': request.POST.get('commit_message'), 'sourcescraper': sourcescraper}
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
    return_url = reverse('frontpage')
    language = language.lower()
    
    codemirrorversion = request.GET.get('codemirrorversion', '')
    if not re.match('[\d\.\w]+$', codemirrorversion):
        codemirrorversion = settings.CODEMIRROR_VERSION

    draftscraper = request.session.get('ScraperDraft', None)
    
    # if this is a matching draft scraper pull it in
    if draftscraper and draftscraper.get('scraper', None) and draftscraper.get('scraper').short_name == short_name:
        scraper = draftscraper.get('scraper', None)
        code = draftscraper.get('code', ' missing')
        rev = 'draft'
    
    # Load an existing scraper in preference
    elif short_name is not "__new__":
        scraper = get_code_object_or_none(models.Code, short_name=short_name)
        if not scraper:
            return code_error_response(models.Code, short_name=short_name, request=request)
        status = vc.MercurialInterface(scraper.get_repo_path()).getstatus(scraper, -1)
        code = status["code"]
        assert 'currcommit' not in status and not status['ismodified']
        rev = status['prevcommit']

        return_url = reverse('code_overview', args=[scraper.wiki_type, scraper.short_name])
        if not scraper.published:
            commit_message = 'Scraper created'

    # Invent a new scraper
    else:
        if language not in ['python', 'php', 'ruby']:
            language = 'python'

        scraper = None
        if wiki_type == 'scraper':
            scraper = models.Scraper()
        elif  wiki_type == 'view':
            scraper = models.View()
        else:
            raise Exception, "Invalid wiki type"

        startupcode = blankstartupcode[wiki_type][language]
        statuptemplate = request.GET.get('template', False)
        if statuptemplate:
            try:
                templatescraper = models.Code.objects.get(published=True, language=language, short_name=statuptemplate)  # wiki_type as well?
                startupcode = templatescraper.saved_code()
            except models.Code.DoesNotExist:
                startupcode = startupcode.replace("Blank", "Missing template for")
            
        # replaces the phrase: sourcescraper = 'working-example' with sourcescraper = 'replacement-name'
        inputscrapername = request.GET.get('sourcescraper', False)
        if inputscrapername:
            startupcode = re.sub('''(?<=sourcescraper = ["']).*?(?=["'])''', inputscrapername, startupcode)
        
        scraper.language = language
        code = startupcode
        rev = None

    # if it's a post-back (save) then execute that
    if request.POST:
        return saveeditedscraper(request, scraper)
    else:
        # Else build the page
        form = forms.editorForm(instance=scraper)
        form.fields['code'].initial = code

        tutorial_scrapers = models.Code.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')

    #if a source scraper has been set, then pass it to the page
    source_scraper = ''
    if scraper.wiki_type == 'view' and request.GET.get('sourcescraper', False):
       source_scraper =  request.GET.get('sourcescraper', False)

    context = {}
    context['form']             = form
    context['scraper']          = scraper
    context['user']             = request.user
    context['source_scraper']   = source_scraper
    context['quick_help_template'] = 'codewiki/includes/%s_quick_help_%s.html' % (scraper.wiki_type, scraper.language.lower())
    context['selected_tab']     = 'code'
    context['rev']              = rev
    context['codemirrorversion']= codemirrorversion
    
    return render_to_response('codewiki/editor.html', context, context_instance=RequestContext(request))


def edittutorial(request, short_name):
    code = get_code_object_or_none(models.Code, short_name=short_name)
    if not code:
        return code_error_response(models.Code, short_name=short_name, request=request)

    qtemplate = "?template="+code.short_name
    return HttpResponseRedirect(reverse('editor', args=[code.wiki_type, code.language]) + qtemplate)



