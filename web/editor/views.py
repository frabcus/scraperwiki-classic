from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
import forms
from scraper.models import Scraper as ScraperModel
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
  
  if short_name:
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
  else:
    scraper = ScraperModel(title=template.default()['title'])
    

  
  if request.method == 'POST':
    form = forms.editorForm(request.POST)
    action = request.POST.get('action')
    if action == "Commit":
      # Commit...
      message = "Scraper Comitted"
    elif action == "Save":
      if form.is_valid():      
        scraperForm = form.save(commit=False)
        scraperForm.code = request.POST['code']
        scraperForm.short_name = short_name
        scraperForm.created_at = scraper.created_at
        scraperForm.save()
        message = "Scraper Saved"
        return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : scraperForm.short_name}))
      
    elif action == "Run":
      # Run...
      message = "Scraper Run"
    else:
      message = ""
  else:
    
    form = forms.editorForm(instance=scraper)
    if short_name:
      form.fields['code'].initial = "scraper.current_code()"
    else:
      form = forms.editorForm(template.default())

  return render_to_response('editor.html', {'scraper':scraper, 'form':form}, context_instance=RequestContext(request)) 
  
  
  
  
  