
from os.path import exists

# This shouldn't be needed, however in some cases the buildout version of
# django (in bin/django) may not make the paths correctly
import sys
sys.path.append('web')

# Django settings for scraperwiki project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# ALTER DATABASE scraperwiki CHARACTER SET=utf8;

try:
  from localsettings import * 
except:
  print """You do not appear to have a database setup defined, if you are running this on a development
  environment, then you need to copy localsettings.py.example to localsettings.py and edit it for your personal settings.
  If this message is displayed in a production environment, then it has not been set up correctly."""
  sys.exit()
 
TIME_ZONE = 'London/England'
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"


MEDIA_DIR = SCRAPERWIKI_DIR + 'media'
MEDIA_ADMIN_DIR = SCRAPERWIKI_DIR + 'media-admin'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a trailing slash.
MEDIA_ROOT = URL_ROOT + 'media/'
CODEMIRROR_ROOT = MEDIA_ROOT + "CodeMirror-0.63/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a trailing slash.
ADMIN_MEDIA_PREFIX = URL_ROOT + 'media-admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x*#sb54li2y_+b-ibgyl!lnd^*#=bzv7bj_ypr2jvon9mwii@z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    SCRAPERWIKI_DIR + 'templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'south',
    'frontend',
	'scraper',
	'notification',
	'page_cache',
)
#    'codewiki',
# removed from installed apps so as to exclude them from the admin interface.
#    'blog',

# tell Django that the frontent user_profile model is to be attached to the user model in the admin side.
AUTH_PROFILE_MODULE = 'frontend.UserProfile'

# Cal Henderson - youtube presentation on Django
# rsvg-convert 
