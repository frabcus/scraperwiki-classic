import re, sys, os, datetime

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


# 
# the wrapper of the FireStarter called from django so we can work out what settings we're going to need to program it with
#
def firestartermethodcall(scraper, codefunction):

    # desperate measure to get to the place where the FireStarter module can be loaded
    sys.path.append(os.path.join(settings.HOME_DIR, "UML", "Server", "scripts"))
    import FireStarter
    firestarter = FireStarter.FireStarter()
    
    # set lots of interesting parameters and controls here
    firestarter.setCPULimit(5)  # integer seconds
    firestarter.addAllowedSites('.*\.gov\.uk')
    firestarter.addPaths('/scraper/scrapers')
    firestarter.addPaths('/home/mike/ScraperWiki/scrapers')
    firestarter.setTraceback ('html')

#    pythoncodeline = "import sys; sys.path.append('%s'); import %s; %s.%s" % (settings.SMODULES_DIR, scraper.short_name, scraper.short_name, codefunction)
    pythoncodeline = "import %s; %s.%s" % (scraper.short_name, scraper.short_name, codefunction)
    print pythoncodeline
    fin = firestarter.execute(pythoncodeline, True)
    
    # should encode this quickly as fin.readlines() in FireStarter itself
    res = [ ]
    try:
        while True:
            line  = fin.readline()
            if not line:
                break
            res.append(re.sub("<", "&lt;", line) + '<br/>')
    except FireStarter.FireError, e :
#      res.append(re.sub("<", "&lt;", str(e)))
       res.append(str(e))

    return res 


# the form that puts out and loads the code for the scraper
class editorForm(forms.Form):   # don't know what ModelForm does
  short_name = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
  starttime  = forms.DateTimeField(widget=forms.TextInput(attrs={"readonly":True}))
  username   = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
  codearea   = forms.CharField(widget=forms.Textarea({'cols':'80', 'rows':'10', 'style':'width:90%'}))
  editorcoderaw = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))


# the form that puts out and loads the code for the scraper 
# (this might be impractical because it makes it impossible to put the Run button next to the Save button)
class runForm(forms.Form):   
  short_name = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
  starttime  = forms.DateTimeField(widget=forms.TextInput(attrs={"readonly":True}))
  username   = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
  codeline   = forms.CharField(widget=forms.TextInput())


#
# this takes the short_name which is the name of the scraper, and redirects the buttons to the savecommit action
#
def edit(request, short_name):
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # the default output is an invalid date for the field
  
  editorcoderaw = reverse('editor_raw', kwargs={'short_name':scraper.short_name})
  editorform = editorForm({"short_name":short_name, "codearea":scraper.saved_code(), "starttime":nowtime, "username":request.user, "editorcoderaw":editorcoderaw})
  defaultcodeline = "Parse()"  # could be a user preference that is saved whenever it is changed
  runform = runForm({"short_name":short_name, "codeline":defaultcodeline, "starttime":nowtime, "username":request.user})
  
  # set the url called when the run button is pressed
  # this MUST have the same domain as the url of form, so this 9004 port method can't work with ajax -- only with specially made up iframe as a target
  # possibly the rerouting to port 9004 could be done via some magic apache rewrite of //localhost/9004/
  # runactionurl = "http://localhost:9004"
  runactionurl = reverse('editor_run', kwargs={'short_name':scraper.short_name})
 
  params = {'scraper':scraper, 'short_name':short_name, 'editorform':editorform, 'runform':runform, 'runactionurl':runactionurl }
  return render_to_response('editor.html', params, context_instance=RequestContext(request)) 


#
# outputs the code in a page on its own so we can do the reload button
#
def raw(request, short_name):
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  return HttpResponse(scraper.saved_code(), mimetype="text/plain")

#
# handles the running of the script when the Run button (in its own form) is pressed
#
def run(request, short_name):

  if request.method != 'POST':
    return HttpResponse(content="Error: no POST")
  
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  runform = runForm(request.POST)

  if not runform.is_valid(): 
    return HttpResponse(content="Error: invalid form " + re.sub("<", "&lt;", str(runform.errors)))
  
  codefunction = runform.cleaned_data['codeline']

  #difflist = directsubprocessruntempfile(scraper, codefunction)   # for running the prototype method
  #difflist = localhostfireboxurlcall(scraper, codefunction)       # for running with a call to the firebox through http://localhost:9004
  difflist = firestartermethodcall(scraper, codefunction)          # would require import FireStarter and to make lots of interesting settings to show what can be done
  
  # return the diff of the save in the #outputarea box 
  return HttpResponse(content="".join(difflist))
  
  
#
# the save and commit action buttons from the editor, whose output goes into the #outputarea window
# also temporary implements a saveandrun button 
#
def savecommit(request, short_name):
  if request.method != 'POST':
    return HttpResponse(content="Error: no POST")
  
  action = request.POST.get('action', 'save').lower()  # needs a default value because Control-S calls submit without any actions
  
  # recover the scraper we are saving to
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  editorform = editorForm(request.POST)
  if not editorform.is_valid(): 
    return HttpResponse(content="Error: invalid form " + re.sub("<", "&lt;", str(editorform.errors)))
  
  # unnecessary, but a sanity check
  if editorform.cleaned_data['short_name'] != short_name:
    return HttpResponse(content="Error: disagreement between short_names")
    
  # produce the diff file to indicate to the user exactly what they changed
  submittedcode = editorform.cleaned_data['codearea']
  currentcode = scraper.saved_code()  
  if currentcode != submittedcode:
    difftext = difflib.unified_diff(currentcode.splitlines(), submittedcode.splitlines())
    difflist = [ diffline  for diffline in difftext  if not re.match("\s*$", diffline) ]
    difflist.insert(0, "SAVING:" + action)
  else:
    difflist = [ "NO CHANGE:" + action ]
    
  # attach the code to the scraper and use a function in vc.py which knows about the code member value to save it
  scraper.code = submittedcode
  bcommit = (action == "commit and close")
  scraper.save(commit=bcommit)
  
  # run the code directly using the saveandrun button, 
  # -- useful temporarily, but intended to become deprecated 
  if action == "saveandrun":
    #difflist = directsubprocessruntempfile(scraper, "Parse()")   # for running the prototype method
    difflist = localhostfireboxurlcall(scraper, "Parse()")        # for running with a call to the firebox through http
    #difflist = firestartermethodcall(scraper, "Parse()")         # would require import FireStarter and to make lots of interesting settings to show what can be done
    
    
  # return the diff of the save in the #outputarea box 
  return HttpResponse(content="\n".join(difflist))
  
  
