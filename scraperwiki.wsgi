import sys
import site
import os

vepath = '/var/www/dev.scraperwiki.com/lib/python2.5/site-packages'

prev_sys_path = list(sys.path)
# add the site-packages of our virtualenv as a site dir
site.addsitedir(vepath)
# add the app's directory to the PYTHONPATH
sys.path.append('/var/www/dev.scraperwiki.com/')
sys.path.append('/var/www/dev.scraperwiki.com/web')

# reorder sys.path so new directories from the addsitedir show up first
new_sys_path = [p for p in sys.path if p not in prev_sys_path]
for item in new_sys_path:
    sys.path.remove(item)
sys.path[:0] = new_sys_path

sys.stdout = sys.stderr
print >> sys.stderr, sys.path


# import from down here to pull in possible virtualenv django install
from django.core.handlers.wsgi import WSGIHandler
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
application = WSGIHandler()
