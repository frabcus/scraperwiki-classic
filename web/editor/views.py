import datetime
import re

from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from scraper.models import Scraper as ScraperModel, UserScraperRole, ScraperDraft
from scraper import template

from django import forms
import difflib
import settings


# various scraper execution functions which can be applied by a developer/demonstrater can to get it 
# temporarily working in order not to get sidetracked into debugging something very very difficult 
# when they could be doing something productive

#
# really crude function from the prototype version that will work when all else fails!  
#
def directsubprocessruntempfile(scraper, codefunction):
    import tempfile, subprocess
    fout = tempfile.NamedTemporaryFile(suffix=".py")
    pythoncodeline = "import %s; %s.%s" % (scraper.short_name, scraper.short_name, codefunction)
    fout.write(pythoncodeline)
    fout.flush()
    cmd = "python %s" % (fout.name)
    env = { "DJANGO_SETTINGS_MODULE":'settings', "PYTHONPATH":"%s:%s" % (settings.SMODULES_DIR, settings.SCRAPERWIKI_DIR) }
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, env=env)
    res = p.stdout.readlines()
    fout.close()   # deletes the temporary file
    return res


#
# a crude wrapper of the localhost firebox interface that may or may not get called directly from the browser in the future
#
def localhostfireboxurlcall(scraper, codefunction):
    import urllib
    
    # desperate forcing to get the path right so it can execute a scraper
    pythoncodeline = "import sys; sys.path.append('%s'); import %s; %s.%s" % (settings.SMODULES_DIR, scraper.short_name, scraper.short_name, codefunction)
    #pythoncodeline = "import sys; print sys.path"  # useful for debugging
    fireboxurl = "http://localhost:9004?" + urllib.urlencode([("code", pythoncodeline)])
    fin = urllib.urlopen(fireboxurl)
    res = [ re.sub("<", "&lt;", lin)  for lin in fin.readlines() ]
    fin.close()   
    return res


# the form that puts out and loads the code for the scraper
class editorForm(forms.Form):   # don't know what ModelForm does
  short_name = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
  starttime  = forms.DateTimeField(widget=forms.TextInput(attrs={"readonly":True}))
  code       = forms.CharField(widget=forms.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))


# this takes the short_name which is the name of the scraper, and redirects the buttons to the savecommit action
def edit(request, short_name):
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # the default output is an invalid date for the field
  form = editorForm({"short_name":short_name, "code":scraper.saved_code(), "starttime":nowtime})
  params = {'scraper':scraper, 'form':form, 'short_name':short_name }
  return render_to_response('editor.html', params, context_instance=RequestContext(request)) 


# not called yet
def run(request, short_name):
  return HttpResponse(content="nothing " )
  
# the save and commit action buttons from the editor, whose output goes into the #outputarea window
# also implements a saveandrun button 
def savecommit(request, short_name):
  if request.method != 'POST':
    return HttpResponse(content="Error: no POST")
  
  action = request.POST.get('action').lower()
  
  # recover the scraper we are saving to
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  form = editorForm(request.POST)
  print str(form.errors)
  if not form.is_valid(): 
    return HttpResponse(content="Error: invalid form " + str(form.errors))
  
  # unnecessary, but a sanity check
  if form.cleaned_data['short_name'] != short_name:
    return HttpResponse(content="Error: disagreement between short_names")
    
  # produce the diff file so we can output to the user exactly what they have saved
  submittedcode = form.cleaned_data['code']
  currentcode = scraper.saved_code()  
  difftext = difflib.unified_diff(currentcode.splitlines(), submittedcode.splitlines())
  difflist = [ diffline  for diffline in difftext  if not re.match("\s*$", diffline) ]
  difflist.insert(0, "SAVING:" + action)
  
  # attach the code to the scraper and use a function in vc.py which knows about the code member value to save it
  scraper.code = submittedcode
  bcommit = (action == "commit and close")
  scraper.save(commit=bcommit)
  
  # run the code directly using the saveandrun button, which is useful now, but may become deprecated 
  if action == "saveandrun":
    #difflist = directsubprocessruntempfile(scraper, "Parse()")   # for running the prototype method
    difflist = localhostfireboxurlcall(scraper, "Parse()")        # for running with a call to the firebox through http
    
    # not done yet -- mike?
    #difflist = firestartermethodcall(scraper, "Parse()")         # would require import FireStarter and to make lots of interesting settings to show what can be done
    
    
  # return the diff of the save in the #outputarea box 
  return HttpResponse(content="\n".join(difflist))
  
  
