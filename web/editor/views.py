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
  This is the main editor view.
  
  Arguements:
  
    - `scraper_id` (int, optional) PK of the Scraper from web.scrapers.models
    
  If the scraper_id arguement supplied:
    1) Load the Scraper object (or 404 if no scraper with that ID)
    2) Load the file from mercurial
    3) Populate the editor form with the correct values and return
  
  If the scraper_id is not supplied:
    1) Crate a Scraper object with a psudo title and template code and return
  
  """

  if request.session.get('ScraperDraft', False):
    scraper = ScraperModel(request.session['ScraperDraft'])
  else:
    if short_name:
      scraper = get_object_or_404(ScraperModel, short_name=short_name)
    else:
      scraper = ScraperModel(title=template.default()['title'])
    

  message = ""
  
  if request.method == 'POST' or bool(re.match('save|commit', request.GET.get('action', ""))):

    form = forms.editorForm(request.POST)
    if form.is_valid():
      scraperForm = form.save(commit=False)
      scraperForm.code = request.POST['code']
      scraperForm.short_name = short_name
      scraperForm.pk = scraper.pk
      scraperForm.created_at = scraper.created_at
      
      action = request.POST.get('action').lower()

      if action == "save" or action == "commit": 
        if scraper.created_at == None:
          scraper.created_at = datetime.datetime.today()
      
        if request.user.is_authenticated():
          # User logged in, so save or commit the scraper

          scraperForm.status = 'Published'
            
          if action == "commit":
            message = "Scraper Comitted"
            scraperForm.save(commit=True)
        
          scraperForm.save()
          scraper = scraperForm
          
          if scraper.owner():
            # Set the owner.
            # If there is already an owner, and it is not this user, mark this user as an editor
            # If the scraper has no owner, then the current user taken ownership
            if scraper.owner().pk != request.user.pk:
              scraper.add_user_role(request.user, 'editor')
          else:
            scraper.add_user_role(request.user, 'owner')
          
          # If the scraper saved, then we can delete the draft  
          if request.session.get('ScraperDraft', False):
            del request.session['ScraperDraft']        

        else:

          # User not logged in
          scraperForm.action = action
          request.session['ScraperDraft'] = scraperForm
          return HttpResponseRedirect(reverse('login'))
          
        message = "Scraper Saved"
        return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : scraperForm.short_name}))
      
      elif action == "run":
        # Run...
        # This shouldn't happen, as 'run' should be caught by javascript in the editor
        message = "You need JavaScript to run script in the browser."
  else:
    
    form = forms.editorForm(instance=scraper)
    if short_name:
      form.fields['code'].initial = scraper.saved_code()
    else:
      form = forms.editorForm(template.default())

  return render_to_response('editor.html', {'scraper':scraper, 'form':form, 'message' : message}, context_instance=RequestContext(request)) 
  
  
  
  
  