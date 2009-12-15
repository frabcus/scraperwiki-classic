from os.path import exists, join

# This shouldn't be needed, however in some cases the buildout version of
# django (in bin/django) may not make the paths correctly
import sys
sys.path.append('web')

# Django settings for scraperwiki project.


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
MEDIA_URL = '/media/'
MEDIA_ADMIN_DIR = SCRAPERWIKI_DIR + 'media-admin'
LOGIN_URL = '/login/'

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
    'django_notify.middleware.NotificationsMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    SCRAPERWIKI_DIR + 'templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.core.context_processors.auth',
  'django.core.context_processors.debug',
  'django.core.context_processors.i18n',
  'django.core.context_processors.media',
  'django.core.context_processors.request',
  'django_notify.context_processors.notifications',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'registration',
    'south',
    'profiles',
    'frontend',
  	'scraper',
  	'notification',
  	'editor',
  	'contact_form',
  	'payment',  	
  	'market',
  	'piston',
  	'api',
    #'debug_toolbar',
  	'django_notify',
  	'tagging',
  	'django.contrib.humanize',
  	'paypal.standard.ipn',
)


ACCOUNT_ACTIVATION_DAYS = 14

# tell Django that the frontent user_profile model is to be attached to the user model in the admin side.
AUTH_PROFILE_MODULE = 'frontend.UserProfile'

# Cal Henderson - youtube presentation on Django
# rsvg-convert 

INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_CONFIG = {
  'INTERCEPT_REDIRECTS' : False
}


NOTIFICATIONS_STORAGE = 'session.SessionStorage'
REGISTRATION_BACKEND = "registration.backends.default.DefaultBackend"


# define default directories needed for paths to run scrapers
SCRAPER_LIBS_DIR = join(HOME_DIR, "scraperlibs")
CODEMIRROR_URL = MEDIA_URL + "CodeMirror-0.64/"

#send broken link emails
SEND_BROKEN_LINK_EMAILS = DEBUG == False

#paypal
PAYPAL_IMAGE = "http://www.paypal.com/en_US/i/btn/btn_paynowCC_LG.gif"
PAYPAL_SANDBOX_IMAGE = PAYPAL_IMAGE

#pagingation
SCRAPERS_PER_PAGE = 60