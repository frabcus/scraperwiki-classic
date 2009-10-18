import sys
sys.path.append('web')

import os
import mercurial
from mercurial import ui as hgui, hg, commands, util, cmdutil
from mercurial.match import always, exact
# from web.localsettings import SMODULES_DIR
SMODULES_DIR = '/tmp/hg/'

def save(paths=[], message="test"): 
  """
  Called each time a file is saved. At this
  point we don't know if it's a new file that needs to be added to version control, or if
  it's been added and just needs to be committed, so use the 'addremove' kwarg.
  """ 

  ui = hgui.ui()
  ui.setconfig('ui', 'interactive', 'off')
  ui.setconfig('ui', 'verbose', 'on')


  reop_path = os.path.normpath(os.path.abspath(SMODULES_DIR))
  r = hg.repository(ui, reop_path, create=False)

  join_files = [path for path in paths] 
  for f in join_files:
    print f
    # commands.add(ui, r, f)
    commands.commit(ui, r, f, addremove=True, message=message)
  return ""

if __name__ == "__main__":
  print SMODULES_DIR
  save(['sym'])