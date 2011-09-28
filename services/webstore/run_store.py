import os, sys

os.environ['WEBSTORE_SETTINGS'] = sys.argv[1]

# Activate the virtual env
instance_dir = '/var/www/scraperwiki/'
pyenv_bin_dir = os.path.join(instance_dir, 'bin')
activate_this = os.path.join(pyenv_bin_dir, 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from webstore.web import app as application
application.debug = False 
application.run( '0.0.0.0', 80 )