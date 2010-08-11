import re
import sys
import os
import datetime
import random
import difflib

try:    import json
except: import simplejson as json

from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from codewiki.models import Scraper as ScraperModel  # is this renaming necessary?
from codewiki.models import UserCodeRole

from codewiki import vc
import forms
import settings


def delete_draft(request):
    if request.session.get('ScraperDraft', False):
        del request.session['ScraperDraft']    
    return HttpResponseRedirect(reverse('editor'))


def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if not code:
        return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
    result = '\n'.join(difflib.unified_diff(scraper.saved_code().splitlines(), code.splitlines(), lineterm=''))
    return HttpResponse("::::" + result, mimetype='text')
    
    
def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        result = "%s:::sElEcT rAnGe:::%s" % (json.dumps(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        result = newcode
    return HttpResponse(result, mimetype="text/plain")

#save a scraper/view
def save_code(scraper, user, code, commaseparatedtags, commitmessage, bnew):
    scraper.update_meta()
    scraper.line_count = int(code.count("\n"))
    scraper.save()   # save the actual object

    mercurialinterface = vc.MercurialInterface()
    mercurialinterface.save(scraper, code)
    if commitmessage:
        rev = mercurialinterface.commit(scraper, message=commitmessage, user=user)
        mercurialinterface.updatecommitalertsrev(rev)

        # refresh the whole set of commit alerts when we have this message
        if commitmessage.strip() == "updatecommitalertsrev" and user.is_staff:
            mercurialinterface.updateallcommitalerts()

    # Add user roles
    if scraper.owner():
        if scraper.owner().pk != user.pk:
            scraper.add_user_role(user, 'editor')
    else:
        scraper.add_user_role(user, 'owner')
        
    # don't know how this somehow magically splits and creates the tags
    scraper.tags = commaseparatedtags
    scraper.save()



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
    draft_commit_message = action.startswith('commit') and session_scraper_draft.get('commit_message') or None
    draft_code = session_scraper_draft.get('code')
    draft_tags = session_scraper_draft.get('commaseparatedtags', '')
    
    save_code(draft_scraper, request.user, draft_code, draft_tags, draft_commit_message, True)
 

    # work out where to send them next
    #go to the scraper page if commited, or the editor if not
    if action == 'save':
        response_url = reverse('editor', kwargs={'short_name' : draft_scraper.short_name})
    elif action == 'commit':
        response_url = reverse('scraper_code', kwargs={'scraper_short_name' : draft_scraper.short_name})

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
    scraper.description = form.cleaned_data['description']    
    scraper.license = form.cleaned_data['license']
    # scraper.run_interval = form.cleaned_data['run_interval']

    # User is signed in, we can save the scraper
    if request.user.is_authenticated():
        commitmessage = action.startswith('commit') and request.POST.get('commit_message', "changed") or None
        save_code(scraper, request.user, code, form.cleaned_data['commaseparatedtags'], commitmessage, False)  # though not always not new
        
        # Work out the URL to return in the JSON object
        url = reverse('editor', kwargs={'short_name':scraper.short_name})
        if action.startswith("commit"):
            url = reverse('scraper_code', kwargs={'scraper_short_name':scraper.short_name})

        # Build the JSON object and return it
        res = json.dumps({'redirect':'true', 'url':url,})    
        return HttpResponse(res)

    # User is not logged in, save the scraper to the session
    else:
        draft_session_scraper = { 'scraper':scraper, 'code':code, 'commaseparatedtags': request.POST.get('commaseparatedtags'), 'commit_message': request.POST.get('commit_message')}
        request.session['ScraperDraft'] = draft_session_scraper

        # Set a message with django_notify telling the user their scraper is safe
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        scraper.action = action

        status = 'Failed'
        response_url = reverse('editor')
        if action == 'save':
            status = 'OK'
        elif action == 'commit':
            response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
            status = 'OK'

        return HttpResponse(json.dumps({'status':status, 'draft':'True', 'url':response_url}))


#Editor form
def edit(request, short_name='__new__', language='Python', tutorial_scraper=None):
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
        scraper = get_object_or_404(ScraperModel, short_name=short_name)
        code = scraper.saved_code()
        commaseparatedtags = ", ".join([tag.name for tag in scraper.tags])
        if not scraper.published:
            commit_message = 'Scraper created'
    
    # Create a new scraper
    else:
        if language not in ['Python', 'PHP', 'Ruby']:
            language = 'Python'

        scraper = ScraperModel()  
        
        startupcode = "# blank"

        if tutorial_scraper:
            startup_scraper = get_object_or_404(ScraperModel, short_name=tutorial_scraper)
            startupcode = startup_scraper.saved_code()
            language = startup_scraper.language
        else:
            # select a startup scraper code randomly from those with the right flag
            startup_scrapers = ScraperModel.objects.filter(published=True, isstartup=True, language=language)
            if len(startup_scrapers):
                startupcode = startup_scrapers[random.randint(0, len(startup_scrapers)-1)].saved_code()

        scraper.license = 'Unknown'
        scraper.language = language
    
        code = startupcode
        commit_message = 'Scraper created'
        commaseparatedtags = ''
        
    # if it's a post-back (save) then execute that
    if request.POST:
        return saveeditedscraper(request, scraper)

    # Build the page
    form = forms.editorForm(instance=scraper)
    form.fields['code'].initial = code
    form.fields['commaseparatedtags'].initial = commaseparatedtags 

    tutorial_scrapers = ScraperModel.objects.filter(published=True, istutorial=True, language=language).order_by('first_published_at')

    return render_to_response('editor/editor.html', {'form':form, 'tutorial_scrapers':tutorial_scrapers, 'scraper':scraper, 'has_draft':has_draft, 'user':request.user}, context_instance=RequestContext(request))
