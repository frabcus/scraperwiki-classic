import sys
# sys.path.append('../../web')

import os
from StringIO import StringIO
import mercurial
from mercurial import ui as hgui, hg, commands, util, cmdutil
from mercurial.match import always, exact

import localsettings
SMODULES_DIR = localsettings.SMODULES_DIR


# from scraper.models import Scraper
# s = Scraper(short_name='test', published_version='1')
# s.save()


def make_file_path(scraper_short_name):
  """
  Scrapers all called __init__.py and are stored in a 
  folder with the same name as the short_name.
  """
  path = "%s%s/__init__.py" % (SMODULES_DIR, scraper_short_name)
  return path

def create(scraper_name):
  scraper_folder_path = "%s%s" % (SMODULES_DIR, scraper_name)
  def make_file(scraper_folder_path):
    print ">>>>>>>>>>>>>"
    print "%s/__init__.py" % scraper_folder_path
    open("%s/__init__.py" % scraper_folder_path, 'w')

  if os.path.exists(scraper_folder_path):
    # the folder exists, but not the file
    make_file(scraper_folder_path)
  else:
    # The folder doesn't exist, so make everything
    os.makedirs(scraper_folder_path)
    make_file(scraper_folder_path)

def save(scraper):
  path = make_file_path(scraper.short_name)
  create(scraper.short_name)
  scraper_file = open(path, 'w')
  scraper_file.write(scraper.code)
  scraper_file.close()

def commit(scraper, message="test"): 
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

  ui.pushbuffer()
  commands.commit(ui, r, path, addremove=True, message=message)
  code = ui.popbuffer()
  return ""

def get_code(scraper_name=None, committed=True):
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
    commands.cat(ui,r,path, output=code, rev='tip')

    return code.getvalue()

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
  
  ui.pushbuffer()
  commands.status(ui,r,'/tmp/hg/test.py', change='tip')
  code = ui.popbuffer() 

  if code != "":
    return True
  else:
    return False



if __name__ == "__main__":
  path = make_file_path('missing_cats')
  save('missing_cats2')
  # save(['sym'])
  