from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import settings
import codewiki.models as models
import os
import re
import datetime
import difflib
import time
import subprocess

import runscrapers

class CodeForm(forms.Form):
    dirname    = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    filename   = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    datetime   = forms.DateTimeField(widget=forms.TextInput(attrs={"readonly":True}))
    outputtype = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    pageid     = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}), required=False)
    code       = forms.CharField(widget=forms.Textarea(attrs={"cols":150, "rows":18}))
    
    def GetScraperFile(self):
        scrapermodule = models.ScraperModule.objects.get(modulename=self.data['dirname'])
        scraperfile = scrapermodule.scraperfile_set.get(filename=self.data['filename'])
        return scraperfile
    
    def GetDiscCode(self):
        scraperfile = self.GetScraperFile()
        return scraperfile.contents()
        
    def DiffCode(self, rcode):
        code = self.GetDiscCode()
        difftext = difflib.unified_diff(code.splitlines(), rcode.splitlines())
        difflist = [ diffline  for diffline in difftext  if not re.match("\s*$", diffline) ]
        return difflist

    def SaveCode(self, rcode):
        scraperfile = self.GetScraperFile()
        scraperfile.SaveFile(rcode)
        return True

newscrapertext = """# New file

def Scrape():
    pass

def DoesApply(reading):
    return False

def Parse(reading):
    return [ ]

def Observe(tailurl):
    print "blank page"
"""

# generate the directory listing in the directory
def codewikilist(request):
    newmodulename = request.POST.get("newfile")
    if newmodulename:
        if re.match("[a-z0-9A-Z_\-]+$", newmodulename):
            fname = os.path.join(settings.SMODULES_DIR, newmodulename)
            if not os.path.exists(fname):
                os.mkdir(fname)
                fnameinit = os.path.join(fname, "__init__.py")
                fout = open(fnameinit, "w")
                fout.write(newscrapertext)
                fout.close()
                newmodule = models.ScraperModule(modulename=newmodulename)
                newmodule.save()
        else:
            newmodulename = "ERROR: Bad file name"
    
    scrapermodules = models.ScraperModule.objects.all()
    return render_to_response('codewikiall.html', { 'scrapermodules':scrapermodules, 'newmodulename':newmodulename, 'settings': settings})


def codewikimodule(request, modulename):
    scrapermodule = models.ScraperModule.objects.get(modulename=modulename)
    
    newfilename = request.POST.get("newfile")
    if newfilename:
        if re.match("[a-z0-9A-Z_\-]+\.py$", newfilename):
            ffname = os.path.join(settings.SMODULES_DIR, scrapermodule.modulename, newfilename)
            if not os.path.exists(ffname):
                fout = open(ffname, "w")
                fout.write("# New file")
                fout.close()
                newfile = models.ScraperFile(module=scrapermodule, filename=newfilename, last_edit=datetime.datetime.fromtimestamp(os.stat(ffname).st_mtime))
                newfile.save()
        else:
            newmodulename = "ERROR: Bad file name"
    
    return render_to_response('codewikimodule.html', { 'scrapermodule':scrapermodule, 'newfilename':newfilename, 'settings': settings})


def codewikinfile(request, modulename, filename):
    scrapermodule = models.ScraperModule.objects.get(modulename=modulename)
    scraperfile = scrapermodule.scraperfile_set.get(filename=filename)
    
    pageid = request.GET.get("pageid")   # from url
    reading = pageid and models.Reading.objects.get(id=pageid) or None
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    outputtype = "normal"
    form = CodeForm({'filename':filename, 'dirname':modulename, 'datetime':nowtime, 'outputtype':outputtype, 'pageid':pageid}) 
    
    # if the form has been returned
    difflist = [ ]
    message = ""
    
    if request.method == 'POST': # If the form has been submitted...
        rform = CodeForm(request.POST) # 
        if rform.is_valid(): # All validation rules pass (how do we check it against the filename and users?)
            rcode = rform.cleaned_data['code']
            outputtype = rform.cleaned_data['outputtype']
            difflist = form.DiffCode(rcode)
            #assert scrapermodule.filename == form.data['filename'], (scrapermodule.filename, form.data['filename'])
            assert scrapermodule.modulename == form.data['dirname'], (scrapermodule.modulename, form.data['dirname'])

            sbutt = rform.data.get("sbutt")
            if sbutt in ["Scrape", "DoesApplyAll", "ParseSingle", "ParseAll", "MakeModels", "Collect" ]:
                if not difflist:
                    if re.match(".*?.py$", filename):
                        message = "OUTPUT FROM RUNNING FILE"
                        bEnableExecution = request.user.is_authenticated()
                        bEnableExecution = True
                        if bEnableExecution:
                            vals = reading and str(reading.id) or ""
                            difflistiter = runscrapers.RunSButtCode(scrapermodule, sbutt, vals)

                            if outputtype == "ajax":
                                return HttpResponse(content=difflistiter)  # should dribble the output out (see runscraper.py for more comments)
                            difflist = list(difflistiter)
                        
                        else:
                            message = 'You must <a href="/admin/">log in</a> to RUN any scripts.  contact julian@goatchurch.org.uk.'

                    else:
                        message = "CANNOT RUN FILE"
                else:
                    message = "SAVE FILE FIRST"
                    form.data['code'] = rcode
            if sbutt == "Save":
                if form.SaveCode(rcode):
                    message = "SAVVVED"
                    # we will reload later
                else:
                    message = "FAILED TO SAVE"
                    form.data['code'] = rcode
            
            if sbutt == "Diffy":
                form.data['code'] = rcode
    
    if not difflist:
        difflist.append("none")
    if message:
        difflist.insert(0, message)

    if 'code' not in form.data:    
        form.data['code'] = form.GetDiscCode()

    
    if outputtype == "ajax":
#        return HttpResponse(content='<br/>'.join(difflist))
        return render_to_response('difflistonly.html', { 'difflist':difflist, 'settings': settings})
    
    filenameother = None
    lang = "python"  # for scraperscript
        
    # quick hack to get observername without .py  this hack is everywhere
    params = { 'form':form, 'lang':lang, 'filenameother':filenameother, 'difflist':difflist, 'reading':reading, 'observername':modulename, 'settings': settings, }
    return render_to_response('codewikinpage.html', params, context_instance=RequestContext(request))



def observer(request, observername, tail):
    exename = os.path.join(settings.SCRAPERWIKI_DIR, "scraperutils.py")
    tail = tail or ""
    tail = re.sub("\(", "\(", tail)
    tail = re.sub("\)", "\)", tail)
    res = runscrapers.RunFileA(exename, "%s %s %s" % (observername, "Observe", tail))
    return HttpResponse(content="".join(list(res)))



def readingsall(request):
    readings = models.Reading.objects.all().order_by('url').order_by('-scrape_time')
    return render_to_response('readingsall.html', {'readings':readings, 'settings': settings})

    
def readingeditpageid(request, pageid):
    scrapertext = models.Reading.objects.get(id=pageid)
    return readingedit(request, scrapertext)


def readingedit(request, reading):
    nowtime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    form = CodeForm({'filename':reading.name, 'dirname':reading.scraper_tag, 'datetime':nowtime}) 
    form.data['code'] = reading and reading.contents() or ""
    urlused = reading and reading.url or ""
    
    message = "hi there"
    difflist = [ ]

    if request.method == 'POST' and scrapertext: # If the form has been submitted...
        rform = CodeForm(request.POST) # 
        if rform.is_valid(): # All validation rules pass (how do we check it against the filename and users?)
            rcode = rform.cleaned_data['code']

            difftext = difflib.unified_diff(form.data['code'].splitlines(), rcode.splitlines())
            difflist = [ diffline  for diffline in difftext  if not re.match("\s*$", diffline) ]

            if "revert" in rform.data:
                pass
            if "save" in rform.data:
                # should really make a diff call here, but save in text anyway
                scrapertext.text = rcode
                scrapertext.save()
                message = "SAVED"
                form.data['code'] = rcode
            if "diff" in rform.data:
                form.data['code'] = rcode

    if not difflist:
        difflist.append("none")
    if message:
        difflist.insert(0, message)

    lang = "xml"
    return render_to_response('scrapertextpage.html', { 'form':form, 'url':urlused, 'difflist':difflist, 'reading':reading, 'lang':lang, 'settings': settings})


def readingrawpageid(request, pageid, fileext):
    scrapertext = models.Reading.objects.get(id=pageid)
    scrapedcode = scrapertext.contents()
    return render_to_response('scrapertextpageview.html', { 'scrapedcode':scrapedcode, 'settings': settings})
    
