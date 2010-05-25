"""
Global settings file.

Everything in here is imported *before* everything in settings.py.

This means that this file is used for default, fixed and global varibles, and
then settings.py is used to overwrite anything here as well as adding settings
particular to the install.

Note that there are no tuples here, as they are immutable. Please use lists, so
that in settings.py we can do list.append()
"""
import os
from os.path import exists, join

# This shouldn't be needed, however in some cases the buildout version of
# django (in bin/django) may not make the paths correctly
import sys
sys.path.append('web')

# Django settings for scraperwiki project.

DEBUG = False
 
TIME_ZONE = 'London/England'
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
SCRAPERWIKI_DIR = ""
MEDIA_DIR = SCRAPERWIKI_DIR + 'media'
MEDIA_URL = 'http://media.scraperwiki.com/'
MEDIA_ADMIN_DIR = SCRAPERWIKI_DIR + '/media-admin'
LOGIN_URL = '/login/'
HOME_DIR = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a trailing slash.
URL_ROOT = ""
MEDIA_ROOT = URL_ROOT + 'media/'
CODEMIRROR_ROOT = MEDIA_ROOT + "CodeMirror-0.67/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a trailing slash.
ADMIN_MEDIA_PREFIX = URL_ROOT + '/media-admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x*#sb54li2y_+b-ibgyl!lnd^*#=bzv7bj_ypr2jvon9mwii@z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'frontend.email_auth.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend'
]

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = [
    SCRAPERWIKI_DIR + 'templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
]

TEMPLATE_CONTEXT_PROCESSORS = [
  'django.core.context_processors.auth',
  'django.core.context_processors.debug',
  'django.core.context_processors.i18n',
  'django.core.context_processors.media',
  'django.core.context_processors.request',
  'django_notify.context_processors.notifications',
  'frontend.context_processors.site',
  'frontend.context_processors.template_settings',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'registration',
    'south',
    
    'profiles',
  	'django.contrib.humanize',
  	'paypal.standard.ipn',
  	'django_notify',
  	'tagging',
  	'mailer',
  	'contact_form',
  	'piston',      # needs 'django-piston' and 'phpserialize'
    
    # the following are scraperwiki apps
    'frontend',
  	'scraper',
  	'notification',
  	'editor',
  	'payment',  	
  	'market',
  	'api',
    'whitelist',
]


ACCOUNT_ACTIVATION_DAYS = 14

# tell Django that the frontent user_profile model is to be attached to the
# user model in the admin side.
AUTH_PROFILE_MODULE = 'frontend.UserProfile'

INTERNAL_IPS = ['127.0.0.1',]


NOTIFICATIONS_STORAGE = 'session.SessionStorage'
REGISTRATION_BACKEND = "registration.backends.default.DefaultBackend"

#tagging
FORCE_LOWERCASE_TAGS = True


# define default directories needed for paths to run scrapers
SCRAPER_LIBS_DIR = join(HOME_DIR, "scraperlibs")
# this value doesn't get through into frontend/base.html, unfortunately
CODEMIRROR_URL = MEDIA_URL + "CodeMirror-0.67/"  

#send broken link emails
SEND_BROKEN_LINK_EMAILS = DEBUG == False

#paypal
PAYPAL_IMAGE = "http://www.paypal.com/en_US/i/btn/btn_paynowCC_LG.gif"
PAYPAL_SANDBOX_IMAGE = PAYPAL_IMAGE

#pagingation
SCRAPERS_PER_PAGE = 60

#API
MAX_API_ITEMS = 500
MAX_API_DISTANCE_KM = 10


# Requited for the template_settings context processor. Each varible listed
# here will be made availible in all templates that are passed the
# RequestContext.  Be carful of listing database and other private settings 
# here
TEMPLATE_SETTINGS = [
 'API_DOMAIN',
 'ORBETED_PORT',
 'ORBETED_DOMAIN',
 'CODE_RUNNING_MODE',
 'CODEMIRROR_URL',
]

#sparklines and graphs
SPARKLINE_MAX_DAYS = 30

try:
    CHANGESET = open('changeset.txt').read()
except Exception, e:
    CHANGESET = "none"
