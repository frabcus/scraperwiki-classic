from lettuce import before
from django.conf import settings
from django.core.management import call_command 
from south.management.commands import patch_for_test_db_setup

@before.harvest
def sync_db(variables):
    patch_for_test_db_setup() 
    call_command('syncdb', interactive=False)

@before.harvest
def set_browser(variables):
    #world.browser = Browser('chrome')
    world.browser = Browser()

@after.harvest
def close_browser(totals):
    failed = False
    for total in totals:
        if total.scenarios_ran != total.scenarios_passed:
            failed = True
    if not failed:
        world.browser.quit()

@world.absorb
class FakeLogin(Client):
    def login(self, username, password):
        user = authenticate(username=username, password=password)
        if user and user.is_active \
                and 'django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE_CLASSES:
            engine = import_module(settings.SESSION_ENGINE)
    
            request = HttpRequest()
            if self.session:
                request.session = self.session
            else:
                request.session = engine.SessionStore()
            login(request, user)
    
            request.session.save()
    
            cookie_data = {
                    'name'    : settings.SESSION_COOKIE_NAME,
                    'value'   : request.session.session_key,
                    'max-age' : None,
                    'path'    : '/',
                    #'domain'  : settings.SESSION_COOKIE_DOMAIN,
                    'expires' : None,
                    }
            return cookie_data
        else:
            raise Exception("Couldn't authenticate")
 
