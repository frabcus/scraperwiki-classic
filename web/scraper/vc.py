import sys
import difflib
import re
sys.path.append('../../web')

import os
from django.conf import settings

import datetime
import time
import mercurial


# The documentation and help strings for this Mercurial interface is inadequate
# The best bet is to look directly at the source code to work out what attributes exist
# mercurial.commands is mostly a wrapper on the functionality of the repo object

class MercurialInterface:
    def __init__(self):
        self.ui = mercurial.ui.ui()
        self.ui.setconfig('ui', 'interactive', 'off')
        self.ui.setconfig('ui', 'verbose', 'on')
        self.repopath = os.path.normpath(os.path.abspath(settings.SMODULES_DIR))  # probably to handle windows values
        
        # danger with member copy of repo as not sure if it updates with commits
        # (definitely doesn't update if commit is done against a second repo object)
        self.repo = hg.repository(self.ui, self.repopath)
    
    
    def save(self, scraper, code):
        scraperfolder = os.path.join(self.repopath, scraper.short_name)
        if not os.path.exists(scraperfolder):
            os.makedirs(scraperfolder)
        scraperpath = os.path.join(scraperfolder, "__init__.py")
        
        fout = open(scraperpath, "w")
        fout.write(code.encode('utf-8'))
        fout.close()
        
    def commit(self, scraper, message="changed", user="unknown"): 
        scraperpath = os.path.join(self.repopath, scraper.short_name, "__init__.py")
        if message is None:
            message = "changed"
  
        self.ui.pushbuffer()
        mercurial.commands.commit(self.ui, self.repo, scraperpath, addremove=True, message=str(message), user=str(user))
        response = self.ui.popbuffer()  # either 'nothing changed\n' or 'committed changeset 28:8ef0500ffeec\n'
        return ""


    def getsavedcode(self, scraper):
        scraperpath = os.path.join(self.repopath, scraper.short_name, "__init__.py")
        fin = open(path,'rU')
        code = fin.read()
        fin.close()
        return code
    
    
    def getcommittedcode(self, scraper):
        scraperpath = os.path.join(self.repopath, scraper.short_name, "__init__.py")
        self.ui.pushbuffer()
        commands.cat(self.ui, self.repo, scraperpath, rev="tip")
        code = self.ui.popbuffer()
        return code


    def getstatus(self, scraper, rev):
        # information about saved file
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        scraperpath = os.path.join(self.repopath, scraperfile)
        lmtime = time.localtime(os.stat(scraperpath).st_mtime)
        filemodifieddate = datetime.datetime(*lmtime[:7])
        
        # what does mercurial say about its status
        modified, added, removed, deleted, unknown, ignored, clean = self.repo.status()
        ismodified = (scraperfile in modified)
        
        result = { "filemodifieddate":filemodifieddate, "ismodified":ismodified }
        
        # adjacent commit informations
        commitlog = self.getcommitlog(scraper)
        if commitlog:
            irev = len(commitlog)
            if rev != -1:
                for lirev in range(len(commitlog)):
                    if commitlog[lirev]["rev"] == rev:
                        irev = lirev
                        break
            if 0 <= irev < len(commitlog):
                result["currcommit"] = commitlog[irev]
            if 0 <= irev - 1 < len(commitlog):
                result["prevcommit"] = commitlog[irev - 1]
            if 0 <= irev + 1 < len(commitlog):
                result["nextcommit"] = commitlog[irev + 1]
                    
        # upgrade the currcommit to contain the code as well
        if "currcommit" in result:
            reversion = self.getreversion(rev)
            result["currcommit"]["code"] = reversion["text"].get(scraperfile)
        return result
    

    def getctxrevisionsummary(self, ctx):
        data = { "rev":ctx.rev(), "userid":ctx.user(), "description":ctx.description() }
        epochtime, offset = ctx.date()
        ltime = time.localtime(epochtime)
        data["date"] = datetime.datetime(*ltime[:7])
        data["files"] = ctx.files()
        return data
            
            
    def getcommitlog(self, scraper):
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        result = [ ]
        for rev in self.repo:
            ctx = self.repo[rev]
            if scraperfile in ctx.files():
                result.append(self.getctxrevisionsummary(ctx))
        return result
            
    
    def getreversion(self, rev):
        ctx = self.repo[rev]
        result = self.getctxrevisionsummary(ctx)
        result["text"] = { }
        for f in ctx.files():
            ftx = ctx.filectx(f)
            result["text"][f] = ftx.data()
        return result
        



def DiffLineSequenceChanges(oldcode, newcode):
    """
    Find the range in the code so we can show a watching user who has clicked
    on refresh what has just been edited this involves doing sequence matching
    on the lines, and then sequence matching on the first and last lines that
    differ    
    """
    
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
    return (matchlinesfront, matchcharsfront, matchlinesbackb, matchcharsbackb)
      #, matchingcblocksback, (len(a[matchlinesbacka]) -
      #  matchingcblocksback[-2][2], len(b[matchlinesbackb]) - 
      #  matchingcblocksback[-2][2]))




# old code

from StringIO import StringIO
from mercurial import ui as hgui, hg, commands, util, cmdutil
from mercurial.match import always, exact
SMODULES_DIR = settings.SMODULES_DIR

def make_file_path(scraper_short_name):
  """
  Scrapers all called __init__.py and are stored in a 
  folder with the same name as the short_name.
  """
  path = "%s%s/__init__.py" % (SMODULES_DIR, scraper_short_name)
  return path.encode()

def create(scraper_name):
  scraper_folder_path = "%s%s" % (SMODULES_DIR, scraper_name)
  def make_file(scraper_folder_path):
    open("%s/__init__.py" % scraper_folder_path, 'w')

  if os.path.exists(scraper_folder_path):
    # the folder exists, but not the file
    make_file(scraper_folder_path)
  else:
    # The folder doesn't exist, so make everything
    os.makedirs(scraper_folder_path)
    make_file(scraper_folder_path)


# the text which is saved comes in as the scraper.code attribute, 
# which doesn't appear anywhere else, and isn't even set during scraper.get_code()
def save(scraper):
  path = make_file_path(scraper.short_name)
  create(scraper.short_name)
  scraper_file = open(path, 'w')

  code = scraper.code
  scraper_file.write(code.encode('utf-8'))

  scraper_file.close()
  

def commit(scraper, message="changed", user="unknown"): 
  """
  Called each time a file is saved. At this
  point we don't know if it's a new file that needs to be added to version control, or if
  it's been added and just needs to be committed, so use the 'addremove' kwarg.
  """
  
  path = make_file_path(scraper.short_name)
  if not os.path.exists(path):
    create(scraper.short_name)
    
  ui = hgui.ui()
  ui.setconfig('ui', 'interactive', 'off')
  ui.setconfig('ui', 'verbose', 'on')

  reop_path = os.path.normpath(os.path.abspath(SMODULES_DIR))
  r = hg.repository(ui, reop_path, create=False)
  
  # Because passing None in an optional argument means it doesn't use the default value
  if message is None:
    message = "changed"
  
  ui.pushbuffer()
  rev = commands.commit(ui, r, path, addremove=True, message=str(message), user=str(user))
  code = ui.popbuffer()  
  return rev

def get_code(scraper_name=None, committed=True, rev='tip'):
  
  """
  Returns the committed file as a string
  """
  path = make_file_path(scraper_name)
  if committed:

    ui = hgui.ui()
    ui.setconfig('ui', 'interactive', 'off')
    ui.setconfig('ui', 'verbose', 'on')

    reop_path = os.path.normpath(os.path.abspath(SMODULES_DIR))
    r = hg.repository(ui, reop_path, create=False)

    code = StringIO("")
    commands.cat(ui,r,path, output=code, rev=rev)

    code_str =  code.getvalue()
    return code_str


  else:
    return open(path,'rU').read()

def been_edited(scraper_name=None):
  """
  Works out if the latest version committed (tip) is different 
  from the version on the file system.
  """
  ui = hgui.ui()
  ui.setconfig('ui', 'interactive', 'off')
  ui.setconfig('ui', 'verbose', 'on')

  reop_path = os.path.normpath(os.path.abspath(SMODULES_DIR))
  r = hg.repository(ui, reop_path, create=False)
  
  path = make_file_path(scraper_name)
  
  ui.pushbuffer()
  commands.status(ui,r,path, change='tip')
  code = ui.popbuffer() 

  if code != "":
    return True
  else:
    return False



