import re
import sys
import os
import datetime
import random
try:
  import json
except:
  import simplejson as json
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from scraper.models import Scraper as ScraperModel  # is this renaming necessary?
from scraper.models import UserScraperRole

from scraper import vc
import forms
import settings


# Delete the draft
def delete_draft(request):
    if  request.session.get('ScraperDraft', False):
        del request.session['ScraperDraft']    
    return HttpResponseRedirect(reverse('editor'))

# Diff
def diff(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
    code = request.POST.get('code', None)    
    if code:
        scraper = get_object_or_404(ScraperModel, short_name=short_name)
        scraper.code = scraper.committed_code()
        return HttpResponse(vc.diff(scraper.code, code), mimetype='text')
    return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')
    
    
def raw(request, short_name=None):
    if not short_name or short_name == "__new__":
        return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
    oldcodeineditor = request.POST.get('oldcode', None)
    newcode = scraper.saved_code()
    if oldcodeineditor:
        sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
        res = "%s:::sElEcT rAnGe:::%s" % (str(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
    else:
        res = newcode
    return HttpResponse(res, mimetype="text/plain")


# Handle Session Draft  
# A non-served page for saving scrapers that have been stored in the session fo non-signed in users
def handle_session_draft(request, action):

    response_url = ''

    # check if they are signed in, if no, they shouldent be here, off to the signin page
    if not request.user.is_authenticated():
        response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
    else:
        #check if anything in the session        
        session_scraper_draft = request.session.get('ScraperDraft', None)

        success = False
        if not session_scraper_draft:
            # Shouldn't be here, go home
            response_url = reverse(frontpage)
        else:
            draft_scraper = session_scraper_draft.get('scraper', None)
            draft_tags = session_scraper_draft.get('tags', '')   
            draft_commit_message = session_scraper_draft.get('commit_message')

            #save or publish the scraper
            if action == 'save':
                draft_scraper.save()
            elif action == 'commit':
                draft_scraper.save(commit=True, message=draft_commit_message, user=request.user.pk)

            # Add tags
            draft_scraper.tags = request.session['ScraperDraft'].get('tags', '')

            # Add user roles
            # TODO: MOVE TO MODEL, THIS IS BUSINESS LOGIC
            if draft_scraper.owner():
                if draft_scraper.owner().pk != request.user.pk:
                    draft_scraper.add_user_role(request.user, 'editor')
            else:
                draft_scraper.add_user_role(request.user, 'owner')

            # work out where to send them next
            #go to the scraper page if commited, or the editor if not
            if action == 'save':
                response_url = reverse('editor', kwargs={'short_name' : draft_scraper.short_name})
            elif action == 'commit':
                response_url = reverse('scraper_code', kwargs={'scraper_short_name' : draft_scraper.short_name})

        #clear the session
        del request.session['ScraperDraft']

    # redirect
    return HttpResponseRedirect(response_url)


#Editor form
def edit(request, short_name='__new__'):

    #have we got an existing draft?
    has_draft = False
    if request.session.get('ScraperDraft', None):
        draft = request.session['ScraperDraft'].get('scraper', None)
        if draft:
          has_draft  = True      
      
    # 1) Get scraper

    if has_draft:
        # Does a draft version exist?
        scraper = draft
        scraper.tags = request.session['ScraperDraft'].get('tags', '')
        scraper.commit_message = request.session['ScraperDraft'].get('commit_message', '')        
    
    elif short_name is not "__new__":
        # Try and load an existing scraper
        scraper = get_object_or_404(ScraperModel, short_name=short_name)
        scraper.code = scraper.saved_code()
        scraper.tags = ", ".join(tag.name for tag in scraper.tags)
        if not scraper.published:
            scraper.commit_message = 'Scraper created'
    
    else:
        # Create a new scraper
        scraper = ScraperModel()
        
        # select a startup scraper value randomly from those with the right flag
        startup_scrapers = ScraperModel.objects.filter(published=True, isstartup=True)

        startupcode = "# blank"
        if len(startup_scrapers):
            startupcode = startup_scrapers[random.randint(0, len(startup_scrapers)-1)].saved_code()
        
        scraper.code = startupcode
        scraper.license = 'Unknown'
        scraper.commit_message = 'Scraper created'

    # 2) If no POST, then just render the page
    if not request.POST:

        # Build the form
        form = forms.editorForm(instance=scraper)
        form.fields['code'].initial = scraper.code
        form.fields['tags'].initial = ", ".join([tag.name for tag in scraper.tags])
    
        tutorial_scrapers = ScraperModel.objects.filter(published=True, istutorial=True)

        return render_to_response('editor/editor.html', {'form':form, 'tutorial_scrapers':tutorial_scrapers, 'scraper':scraper, 'has_draft':has_draft, 'user':request.user}, context_instance=RequestContext(request))        
    
    else:        
        # 3) If there is POST, then use that
        form = forms.editorForm(request.POST, instance=scraper)

        #validate
        if not form.is_valid() or 'action' not in request.POST:
            return HttpResponse(json.dumps({'status' : 'Failed'}))

        action = request.POST.get('action').lower()

        # Save the form  (without committing at first - http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method)
        savedForm = form.save(commit=False)      

        # Add some more fields to the form
        savedForm.code = form.cleaned_data['code']
        savedForm.description = form.cleaned_data['description']    
        savedForm.license = form.cleaned_data['license']
        # savedForm.run_interval = form.cleaned_data['run_interval']

        if request.user.is_authenticated():
            # User is signed in, we can save the scraper
            if action == 'save':
                #save without commiting
                savedForm.save()
            if action.startswith('commit'):          
                message = None
                #set the commit message if present
                if request.POST.get('commit_message', False):
                    message = request.POST['commit_message']
                # save and commit
                savedForm.save(commit=True, message=message, user=request.user.pk)

            # Add user roles
            # MOVE TO MODEL THIS IS BUSINESS LOGIC
            if savedForm.owner():
                if savedForm.owner().pk != request.user.pk:
                    savedForm.add_user_role(request.user, 'editor')
            else:
                savedForm.add_user_role(request.user, 'owner')

            # Add tags (note that we have to do this *after* the scraper has been saved)
            s = get_object_or_404(ScraperModel, short_name=savedForm.short_name)
            s.tags = request.POST.get('tags')

            # Work out the URL to return in the JSON object
            url = reverse('editor', kwargs={'short_name' : savedForm.short_name})
            if action.startswith("commit"):
                url = reverse('scraper_code', kwargs={'scraper_short_name' : savedForm.short_name})

            # Build the JSON object and return it
            res = json.dumps({'redirect':'true', 'url':url,})    
            return HttpResponse(res)

        else:

            # User is not logged in, save the scraper to the session
            draft_session_scraper = { 'scraper':savedForm, 'tags': request.POST.get('tags'), 'commit_message': request.POST.get('commit_message')}
            request.session['ScraperDraft'] = draft_session_scraper

            # Set a message with django_notify telling the user their scraper is safe
            request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
            savedForm.action = action

            status = 'Failed'
            response_url = reverse('editor')
            if action == 'save':
                status = 'OK'
            elif action == 'commit':
                response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
                status = 'OK'

            return HttpResponse(json.dumps({'status' : status, 'draft' : 'True', 'url': response_url}))
