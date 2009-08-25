from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
import settings
import codewiki.models as models
import os
import re
import datetime
import difflib
import time
import subprocess

import runscrapers

bEnableExecution = True

class CodeForm(forms.Form):
    dirname    = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    filename   = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    datetime   = forms.DateTimeField(widget=forms.TextInput(attrs={"readonly":True}))
    outputtype = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}))
    pageid     = forms.CharField(widget=forms.TextInput(attrs={"readonly":True}), required=False)
    code       = forms.CharField(widget=forms.Textarea(attrs={"cols":150, "rows":18}))
    
    def GetDiscCode(self):
        fname = os.path.join(settings.MODULES_DIR, self.data['dirname'], self.data['filename'])
        if os.path.isfile(fname):
            fin = open(fname, "r")
            res = fin.read()
            fin.close()
        else:
            res = None
        return res
        
    def DiffCode(self, rcode):
        code = self.GetDiscCode()
        difftext = difflib.unified_diff(code.splitlines(), rcode.splitlines())
        difflist = [ diffline  for diffline in difftext  if not re.match("\s*$", diffline) ]
        return difflist

    def SaveCode(self, rcode):
        fname = os.path.join(settings.MODULES_DIR, self.data['dirname'], self.data['filename'])
        fout = open(fname, "w")
        res = fout.write(rcode)
        fout.close()
        return True


# generate the directory listing in the directory
def codewikidir(request, dirname, subdirname):
    subdirname = subdirname or ""
    dname = os.path.join(settings.MODULES_DIR, dirname, subdirname)
    
    newfilename = request.POST.get("newfile")
    if newfilename:
        if re.match("[a-z0-9A-Z_\-]+\.py", newfilename):
            fname = os.path.join(settings.MODULES_DIR, dirname, subdirname, newfilename)
            if not os.path.exists(fname):
                fout = open(fname, "w")
                fout.write("# New file")
                fout.close()
                newscraperscript = models.ScraperScript(dirname=dirname, filename=newfilename, last_edit=datetime.datetime.fromtimestamp(os.stat(fname).st_mtime))
                newscraperscript.save()
        else:
            newfilename = "ERROR: Bad file name"
    
    scraperscripts = models.ScraperScript.objects.filter(dirname=dirname)
    
    return render_to_response('codewikidir.html', { 'dirname':dirname, 'scraperscripts':scraperscripts, 'newfilename':newfilename, 'settings': settings})


def codewikipage(request, dirname, filename):
    scraperscript = models.ScraperScript.objects.filter(dirname=dirname, filename=filename)[0]
    pageid = request.GET.get("pageid")   # from url
    reading = pageid and models.Reading.objects.get(id=pageid) or None
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    outputtype = "normal"
    form = CodeForm({'filename':scraperscript.filename, 'dirname':scraperscript.dirname, 'datetime':nowtime, 'outputtype':outputtype, 'pageid':pageid}) 
    
    # if the form has been returned
    difflist = [ ]
    message = ""

    if request.method == 'POST': # If the form has been submitted...
        rform = CodeForm(request.POST) # 
        if rform.is_valid(): # All validation rules pass (how do we check it against the filename and users?)
            rcode = rform.cleaned_data['code']
            outputtype = rform.cleaned_data['outputtype']
            difflist = form.DiffCode(rcode)
            assert scraperscript.filename == form.data['filename']
            assert scraperscript.dirname == form.data['dirname']
            if "revert" in rform.data:
                pass
            brunscrape = "runscrape" in rform.data
            brundoesapply = "rundoesapply" in rform.data
            brunpage = "runparse" in rform.data
            brunparseall = "runparseall" in rform.data
            brunmakemodel = "runmakemodel" in rform.data
            bruncollect = "runcollect" in rform.data
            if brunscrape or brundoesapply or brunpage or brunmakemodel or bruncollect or brunparseall:
                if not difflist:
                    if re.match(".*?.py$", filename):
                        message = "OUTPUT FROM RUNNING FILE"
                        exename = os.path.join(settings.MODULES_DIR, form.data['dirname'], form.data['filename'])
                        if bEnableExecution:
                            if brundoesapply:
                                difflistiter = runscrapers.RunDoesApply(scraperscript)
                            elif brunscrape:
                                difflistiter = runscrapers.RunFileA(exename, "scrape") 
                            elif brunmakemodel:
                                #difflistiter = runscrapers.RunFileA(exename, "makemodel") 
                                difflistiter = runscrapers.RunMakeModels(scraperscript)
                            elif bruncollect:
                                difflistiter = runscrapers.RunFileA(exename, "collect") 
                            elif brunpage:
                                difflistiter = runscrapers.RunParseSingle(scraperscript, reading) 
                            elif brunparseall:
                                difflistiter = runscrapers.RunParseAll(scraperscript) 

                            if outputtype == "ajax":
                                return HttpResponse(content=difflistiter)  # should dribble the output out (see runscraper.py for more comments)
                            difflist = list(difflistiter)
                        
                        else:
                            message = "RUNNING OF FILES disabled.  contact julian@goatchurch.org.uk to enable it."

                    else:
                        message = "CANNOT RUN FILE"
                else:
                    message = "SAVE FILE FIRST"
                    form.data['code'] = rcode
            if "save" in rform.data:
                if form.SaveCode(rcode):
                    message = "SAVVVED"
                    # we will reload later
                else:
                    message = "FAILED TO SAVE"
                    form.data['code'] = rcode
            if "diff" in rform.data:
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
    params = { 'form':form, 'lang':lang, 'filenameother':filenameother, 'difflist':difflist, 'reading':reading, 'observername':filename[:-3], 'settings': settings}
    return render_to_response('codewikipage.html', params)



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
    
