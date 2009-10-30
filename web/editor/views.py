import datetime
import re

from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
import forms
from scraper.models import Scraper as ScraperModel, UserScraperRole, ScraperDraft
from scraper import template

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
  
  
  Arguements:
  
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

  else:
    # No drafts exist...
    if short_name:
      # ...and this is an existing scraper.  Load from the database and disk
      scraper = get_object_or_404(ScraperModel, short_name=short_name)
      scraper.code = scraper.saved_code()
    else:
      # This is a new scraper
      scraper = ScraperModel(**template.default())
      scraper.code = template.default()['code']

  form = forms.editorForm(instance=scraper)
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
        print "is draft"
        form = forms.editorForm(draft.__dict__, instance=draft)
        form.code = draft.code
        action = request.GET.get('action').lower()
      else:
        # The GET action was called incorrectly, so we just redurect to a cleaner URL
        if short_name:
          return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : short_name}))
        else:
          return HttpResponseRedirect(reverse('editor'))
    
    print form.errors
    
    if form.is_valid():
      print "form is valid"
      # Save the form without committing at first
      # (read http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method)
      savedForm = form.save(commit=False)
      
      # Add some more fields to the form
      savedForm.code = form.cleaned_data['code']
      savedForm.short_name = short_name
      
      if hasattr(scraper, 'pk'):
        savedForm.pk = scraper.pk
      savedForm.created_at = scraper.created_at
      if savedForm.created_at == None:
        savedForm.created_at = datetime.datetime.today()

      if request.user.is_authenticated():
        print action
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
        
        
  return render_to_response('editor.html', {'form':form}, context_instance=RequestContext(request)) 
  







  # if request.method == 'POST' or bool(re.match('save|commit', request.GET.get('action', ""))):
  # 
  #   if not form:
  #     if request.POST:
  #       form = forms.editorForm(request.POST)
  #       req_type = 'post'
  #       form.code = request.POST.get('code', '')
  #     else:
  #       if request.session.get('ScraperDraft', False):
  #         form = forms.editorForm(instance=request.session['ScraperDraft'])
  #         form.code = request.session['ScraperDraft'].code
  #       else:
  #         return HttpResponseRedirect(reverse('editor'))
  # 
  #   print form.code
  # 
  #   if form.is_valid():
  #     scraperForm = form.save(commit=False)
  #     scraperForm.code = form.code
  #     scraperForm.short_name = short_name
  #     if 'pk' in dir(scraper):
  #       scraperForm.pk = scraper.pk
  #     scraperForm.created_at = scraper.created_at
  #   
  #     if request.POST:
  #       action = request.POST.get('action').lower()
  #     else:
  #       action = request.GET.get('action').lower()
  #   
  #   
  #     if action == "save" or action == "commit and close": 
  #       if scraper.created_at == None:
  #         scraper.created_at = datetime.datetime.today()
  #   
  #       if request.user.is_authenticated():
  #         # User logged in, so save or commit the scraper
  #       
  #         scraperForm.status = 'Published'
  #         
  #         if action == "commit and close":
  #           message = "Scraper Comitted"
  #           scraperForm.save(commit=True)
  #     
  #         scraperForm.save()
  #         scraper = scraperForm
  #       
  #         if scraper.owner():
  #           # Set the owner.
  #           # If there is already an owner, and it is not this user, mark this user as an editor
  #           # If the scraper has no owner, then the current user taken ownership
  #           if scraper.owner().pk != request.user.pk:
  #             scraper.add_user_role(request.user, 'editor')
  #         else:
  #           scraper.add_user_role(request.user, 'owner')
  #         
  #         # If the scraper saved, then we can delete the draft  
  #         if request.session.get('ScraperDraft', False):
  #           del request.session['ScraperDraft']        
  #       
  #       else:
  # 
  #         # User not logged in
  #         scraperForm.action = action
  #         request.session['ScraperDraft'] = scraperForm
  #         return HttpResponseRedirect(reverse('login'))
  #     
  #       if action == "commit and close":
  #         return HttpResponseRedirect(reverse('scraper_code', kwargs={'scraper_short_name' : scraperForm.short_name}))
  #       message = "Scraper Saved"
  #       return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : scraperForm.short_name}))
  #   
  #     elif action == "run":
  #       # Run...
  #       # This shouldn't happen, as 'run' should be caught by javascript in the editor
  #       message = "You need JavaScript to run script in the browser."
  # else:
  # 
  # 
  # 
  #   if request.session.get('ScraperDraft', False):
  #     scraper = ScraperModel(request.session['ScraperDraft'])
  #   elif short_name:
  #     scraper = get_object_or_404(ScraperModel, short_name=short_name)
  #   else:
  #     scraper = ScraperModel()
  # 
  #   form = forms.editorForm(scraper)
  #   message = ""
  # 
  #   form = forms.editorForm(scraper)
  #   
  #   if short_name:
  #     form.fields['code'].initial = scraper.saved_code()
  #   # elif request.session.get('ScraperDraft', False):
  #   #   form.fields['code'].initial = request.session['ScraperDraft'].code
  #   else:
  #     form = forms.editorForm(template.default())
  # 
  # # del request.session.get('ScraperDraft', False)
  # return render_to_response('editor.html', {'form':form}, context_instance=RequestContext(request)) 
