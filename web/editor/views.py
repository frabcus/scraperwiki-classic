import re
import sys
import os
import datetime

from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from scraper.models import Scraper as ScraperModel, UserScraperRole
from scraper import template
from scraper import vc
import forms
import settings


def delete_draft(request):
  if request.session.get('ScraperDraft', None):
    draft = request.session['ScraperDraft']
    del request.session['ScraperDraft']
    if draft.short_name:
      return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : draft.short_name}))
  return HttpResponseRedirect(reverse('editor'))
    

def save_draft(request):
  print request.session['ScraperDraft']
  draft_form = forms.editorForm(request.POST)
  savedForm = draft_form.save(commit=False)
  savedForm.code = draft_form.cleaned_data['code']
  request.session['ScraperDraft'] = savedForm  
  return HttpResponseRedirect(reverse('editor'))

def diff(request, short_name):
  if not short_name:
    return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
  if request.POST.get('code', False):
    code = request.POST['code']    
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
    scraper.code = scraper.committed_code()
    return HttpResponse(vc.diff(scraper.code, code), mimetype='text')
    

def edit(request, short_name=None):
  """
  This is the main editor view.  Made more complex by bcause of the 
  'lazy registration' model.  This is implemented by creating a copy
  of the editor form in the session, so if this session exists then 
  it should be loaded by default (see below for problems).
  
  The use cases are as follows:
  
  1. Scraper creation.  Scrapers can be run before saving/committing.  
     Display the standard (empty) editor form at /editor.

  2. Scraper editing.  Scrapers can be edited by anyone, but not saved
     unless they are logged in.  Titles can be changed, but not short
     names.  Display the existing editor at /editor/<shortname>
  
  In both the above cases, if a user isn't logged in then the form object
  is saved in to the session and the user is redirected to the log in page
  
  After logging in they are redirected to the scraper they came from and 
  the action they attepted (save or commit) is performed.  If the action 
  is save then they are redirected to the editor page for that scraper, if
  it's commit (and close) then they are redirected to the scrapers main page.
  
  
    - `short_name` (optional) Short name of the Scraper from web.scrapers.models  

  TODO:
    * Only load draft for the correct scraper (sniff short_name, or new)
    * If short_name exists, don't make a new one
    
  """

  draft = request.session.get('ScraperDraft', None)
  # First off, create a scraper instance somehow.
  # Drafts are seen as more 'important' than saved scrapers.
  if draft:
    if draft.short_name:
      # We're working with an existing scraper that has been edited, but not saved
      scraper = draft
      scraper.code = draft.code
    else:
      # This is a new scraper that has been edited, but not saved
      scraper = draft
      scraper.code = draft.code
  else:
    # No drafts exist...
    if short_name:
      # ...and this is an existing scraper.  Load from the database and disk
      scraper = get_object_or_404(ScraperModel, short_name=short_name)
      scraper.code = scraper.saved_code()
    else:
      # This is a new scraper
      scraper = ScraperModel(title=template.default()['title'])
      scraper.code = template.default()['code']

  form = forms.editorForm(scraper.__dict__, instance=scraper)
  form.fields['code'].initial = scraper.code
  
  
  if request.method == 'POST' or bool(re.match('save|commit', request.GET.get('action', ""))):
    if request.POST:
    # If there is POST, then use that as the form
      form = forms.editorForm(request.POST, instance=scraper)
      action = request.POST.get('action').lower()
    else:
      # We only reach here when the GET action is scraper or commit,
      # and that only heppens when the 'draft' feature is being used.
      if draft:
        form = forms.editorForm(draft.__dict__, instance=draft)
        form.code = draft.code
        action = request.GET.get('action').lower()
      else:
        # The GET action was called incorrectly, so we just redurect to a cleaner URL
        if short_name:
          return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : short_name}))
        else:
          return HttpResponseRedirect(reverse('editor'))
    
    if form.is_valid():
      # Save the form without committing at first
      # (read http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method)
      savedForm = form.save(commit=False)

      # Add some more fields to the form
      savedForm.code = form.cleaned_data['code']
      # savedForm.short_name = short_name
      # if hasattr(scraper, 'pk'):
      #   savedForm.pk = scraper.pk

      if request.user.is_authenticated():
        # The user is authenticated, so we can process the form correctly
        if action == 'save':
          savedForm.save()
        if action.startswith('commit'):
          savedForm.save(commit=True)
          
        if savedForm.owner():
          # Set the owner.
          # If there is already an owner, and it is not this user, mark this user as an editor
          # If the scraper has no owner, then the current user taken ownership
          if savedForm.owner().pk != request.user.pk:
            savedForm.add_user_role(request.user, 'editor')
        else:
          savedForm.add_user_role(request.user, 'owner')
        
        # If the scraper saved, then we can delete the draft  
        if request.session.get('ScraperDraft', False):
          del request.session['ScraperDraft']
        
        if action.startswith("commit"):
          return HttpResponseRedirect(reverse('scraper_code', kwargs={'scraper_short_name' : savedForm.short_name}))
        message = "Scraper Saved"
        return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : savedForm.short_name}))
        
      else:
        # Set a message with django_notify
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        savedForm.action = action
        request.session['ScraperDraft'] = savedForm
        return HttpResponseRedirect(reverse('login'))
        
        
  return render_to_response('editor.html', {'form':form, 'scraper' : scraper, 'settings' : settings }, context_instance=RequestContext(request)) 
