import re
import sys
import os
import datetime
try:
  import json
except:
  import simplejson as json
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

# Delete the draft
def delete_draft(request):
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
    #temp variables
    message = 'temporary message'

    # check if they are signed in, if no, they shouldent be here, off to the signin page
    if not request.user.is_authenticated():
        print ">>>>>>> No user found"
        response_url =  reverse('login') + "?next=%s" % reverse('handle_session_draft', kwargs={'action': action})
    else:                    
        print ">>>>>>> Found a user"                     
        #check if anything in the session
        draft_scraper = request.session['ScraperDraft'].get('scraper', None)
        draft_tags = request.session['ScraperDraft'].get('tags', None)        
        success = False
        if not draft_scraper:
            print ">>>>>>> No draft scraper"
            #TODO get the url we came from, if there is nothing in the session we need to send them back there            
            response_url = ''            
        else:
            print ">>>>>>> Found a draft scraper"            
            #save or publish the scraper
            # TODO: check what happens if draft of existing scraper. prevent duplicates        
            if action == 'save':
                print ">>>>>>> Trying to save"
                #TODO: add tags after save
                draft_scraper.save()
            elif action == 'commit':
                print ">>>>>>> Trying to commit"
                draft_scraper.save(commit=True, message=message, user=request.user.pk)


            # Add user roles
            # MOVE TO MODEL THIS IS BUSINESS LOGIC
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
    print response_url
    return HttpResponseRedirect(response_url)

    
#Editor
def edit(request, short_name=None):

    #if no short name, assign a tempory one
    if short_name == None:
      short_name = "__new__" 

    #TODO: remove this - if nothing in the session, clear it
    if not request.session.get('ScraperDraft', None):
        request.session['ScraperDraft'] = {}

    # Get scraper -  either from the database if it already exists, or create a blank one
    if short_name is not "__new__":
        # No drafts exist and this is an existing scraper.  Load from the database and disk
        # This happens after you've pressed the SAVE button
        scraper = get_object_or_404(ScraperModel, short_name=short_name)
        scraper.code = scraper.saved_code()
        # load tags into form (using dict)
        scraper.__dict__['tags'] = ", ".join(tag.name for tag in scraper.tags)
        if not scraper.published:
            #TODO: move this to the model
            scraper.__dict__['commit_message'] = 'Scraper created'
    else:
        # This is a totally brand new scraper, load default code
        scraper = ScraperModel()
        scraper.code = template.default()['code']
        scraper.license = 'Unknown'
        #TODO: move this to the model
        scraper.__dict__['commit_message'] = 'Scraper created'


    # Build the form
    form = forms.editorForm(scraper.__dict__, instance=scraper)
    form.fields['code'].initial = scraper.code
    form.fields['title'].initial = scraper.title
    form.fields['license'].initial = scraper.license
    #form.fields['run_interval'].initial = scraper.run_interval
    
    #have we got an existing draft?
    has_draft = False
    draft = request.session['ScraperDraft'].get('scraper', None)
    if draft:
        has_draft  = True


    #Handle postback
    if not request.POST:
        return render_to_response('editor.html', {'form':form, 'scraper' : scraper, 'has_draft': has_draft}, context_instance=RequestContext(request))        
    else:        
        # If there is POST, then use that as the form
        form = forms.editorForm(request.POST, instance=scraper)
        action = request.POST.get('action').lower()

        #validate
        if form.is_valid():

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
                res = json.dumps({
                'redirect' : 'true',
                'url' : url,
                })    
                return HttpResponse(res)

            else:

                # User is not loged in, save the scraper to the session
                draft_session_scraper = {'scraper': savedForm, 'tags': request.POST.get('tags')}
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
