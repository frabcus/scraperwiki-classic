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
    #firestarter.addPaths('/scraper/scrapers')
    firestarter.addPaths(settings.SMODULES_DIR)  # from localsettings.py
    firestarter.setTraceback ('html')

    #pythoncodeline = "import sys; sys.path.append('%s'); import %s; %s.%s" % (settings.SMODULES_DIR, scraper.short_name, scraper.short_name, codefunction)
    pythoncodeline = "import %s; %s.%s" % (scraper.short_name, scraper.short_name, codefunction)
    print pythoncodeline
    fin = firestarter.execute(pythoncodeline, True)
    if not fin:
        yield "Total error here: Is your UML running?"
        return
    
    # we could be writing the results out to a log file associated to the scraper 
    # so that someone watching and reloading can also load the output 
    # (saved in some media/ directory, say, in a way that informs the webserver to keep the 
    # http connection open when the scraper is still running).  
    # if this was done by polling, then the watcher would experience streaming of a sort.  
    # if it gave good enough results, we could use it for the main user
    fout = None # scraper.outputlog.open()
    
    try:
        while True:
            line = fin.readline()
            if not line:
                break
            
            # necessary to escape the symbols and add breaks when it is outputting to a div block
            # this is not necessary if the output is to a textarea (which might be better)
            if fout:
                fout.write(line)
            yield re.sub("<", "&lt;", line) + '<br/>\n'
    
    except FireStarter.FireError, e :
       # yield re.sub("<", "&lt;", str(e))
       yield str(e)   # not escaped (is the exception value already marked up?)  
       # this could also output a delimited/parsed string that javascript can decode in order to take the editor to the correct line
       if fout:
           fout.write(line)
    if fout:
        fout.close()
        

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
# and if it receives code through a POST, then it tells the browser where the differences are
#
def raw(request, short_name):
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  oldcodeineditor = request.POST.get('oldcode', '')
  newcode = scraper.saved_code()
  if oldcodeineditor:
      sequencechange = DiffLineSequenceChanges(oldcodeineditor, newcode)
      res = "%s:::sElEcT rAnGe:::%s" % (str(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
  else:
      res = newcode
  return HttpResponse(res, mimetype="text/plain")



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
  runiter = firestartermethodcall(scraper, codefunction)      # would require import FireStarter and to make lots of interesting settings to show what can be done
  
  # passes the iterator into django as though it can handle streaming (even though it cannot without the patch or waiting for version 1.4)
  return HttpResponse(content=runiter)
  
  
  
# find the range in the code so we can show a watching user who has clicked on refresh what has just been edited
# this involves doing sequence matching on the lines, and then sequence matching on the first and last lines that differ
def DiffLineSequenceChanges(oldcode, newcode):
    a = oldcode.splitlines()
    b = newcode.splitlines()
    sqm = difflib.SequenceMatcher(None, a, b)
    matchingblocks = sqm.get_matching_blocks()  # [ (i, j, n) ] where  a[i:i+n] == b[j:j+n].
    assert matchingblocks[-1] == (len(a), len(b), 0)
    matchlinesfront = (matchingblocks[0][:2] == (0, 0) and matchingblocks[0][2] or 0)
    
    if (len(matchingblocks) >= 2) and (matchingblocks[-2][:2] == (len(a) - matchingblocks[-2][2], len(b) - matchingblocks[-2][2])):
        matchlinesback = matchingblocks[-2][2]
    else:
        matchlinesback = 0
    
    matchlinesbacka = len(a) - matchlinesback - 1
    matchlinesbackb = len(b) - matchlinesback - 1
    
    # no difference case
    if matchlinesbackb == -1:
        return (0, 0, 0, 0)  
    
    # lines have been cleanly deleted, so highlight first character where it happens
    if matchlinesbackb < matchlinesfront:
        assert matchlinesbackb == matchlinesfront - 1
        return (matchlinesfront, 0, matchlinesfront, 1)
    
    # find the sequence start in first line that's different
    sqmfront = difflib.SequenceMatcher(None, a[matchlinesfront], b[matchlinesfront])
    matchingcblocksfront = sqmfront.get_matching_blocks()  # [ (i, j, n) ] where  a[i:i+n] == b[j:j+n].
    matchcharsfront = (matchingcblocksfront[0][:2] == (0, 0) and matchingcblocksfront[0][2] or 0)
    
    # find sequence end in last line that's different
    if (matchlinesbacka, matchlinesbackb) != (matchlinesfront, matchlinesfront):
        sqmback = difflib.SequenceMatcher(None, a[matchlinesbacka], b[matchlinesbackb])
        matchingcblocksback = sqmback.get_matching_blocks()  
    else:
        matchingcblocksback = matchingcblocksfront
    
    if (len(matchingcblocksback) >= 2) and (matchingcblocksback[-2][:2] == (len(a[matchlinesbacka]) - matchingcblocksback[-2][2], len(b[matchlinesbackb]) - matchingcblocksback[-2][2])):
        matchcharsback = matchingcblocksback[-2][2]
    else:
        matchcharsback = 0
    matchcharsbackb = len(b[matchlinesbackb]) - matchcharsback
    return (matchlinesfront, matchcharsfront, matchlinesbackb, matchcharsbackb)  #, matchingcblocksback, (len(a[matchlinesbacka]) - matchingcblocksback[-2][2], len(b[matchlinesbackb]) - matchingcblocksback[-2][2]))
  
  

#
# the save and commit action buttons from the editor, whose output goes into the #outputarea window
# also temporary implements a saveandrun button 
#
def savecommit(request, short_name):
  if request.method != 'POST':
    return HttpResponse(content="Error: no POST")
  
  # requires a default value because Control-S calls submit without any actions
  action = request.POST.get('action', 'save').lower()  
  # valid actions are 'save', 'commitandclose', 'saveandrun' (hidden)
  
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
  sequencechange = DiffLineSequenceChanges(currentcode, submittedcode)
  if sequencechange == (0,0,0,0):
    difflist = [ "NO CHANGE:" + action ]
  else:
    difflist = [ "SAVING:" + action, str(sequencechange) ]
    
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
  return HttpResponse(content="<br/>\n".join(difflist))
  
  
