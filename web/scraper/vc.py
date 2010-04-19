import sys
import difflib
import re
sys.path.append('../../web')

import os
from StringIO import StringIO
import mercurial
from mercurial import ui as hgui, hg, commands, util, cmdutil
from mercurial.match import always, exact

from django.conf import settings
SMODULES_DIR = settings.SMODULES_DIR


# from scraper.models import Scraper
# s = Scraper(short_name='test', published_version='1')
# s.save()


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
  return ""

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
    print code_str
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

def diff(a, b=None, rev='tip', scraper_name=None):
  """
  Given a scraper name, allow browsing of diffs.
  
  - `a`: Code to diff against.
  - `b`: (optional) The other half of the code to diff against.
  - `rev`: (optional) The revistion to diff against.
  
  `b` and `rev` are optional.  If `b` is not provided diff is performed
  against the 'tip' revision of the code.  If 'rev' is provided then 
  we diff against that revision.  If 'b' and 'rev' are provided then
  'rev is ignored.
  
  """
  if not b:
    b = get_code(scraper_name, rev=rev)
  
  x = '\n'.join(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=''))
  return x
    # yield line

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







if __name__ == "__main__":
  # path = make_file_path('missing_cats')
  x = diff('missing_cats2', scraper_name='asd-1')
  while x:
    print dir(x)
    x.next()
  # save(['sym'])
