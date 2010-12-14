from django.contrib.sites.models import Site, RequestSite
from django.utils.safestring import mark_safe
from frontend.models import Message
import settings
import datetime

# Taken from http://www.djangosnippets.org/snippets/1197/
def site(request):
    """
    Grabs the 'site' app's information, and makes it availile to templates
    """
    site_info = {'protocol': request.is_secure() and 'https' or 'http'}
    if Site._meta.installed:
        site_info['domain'] = Site.objects.get_current().domain
    else:
        site_info['domain'] = RequestSite(request).domain
    return site_info
    

def template_settings(request):
    """
    Looks for a list in settings (and therefore any varible imported in to the
    global namespace in settings, such as 'localsettings') called 
    'TEMPLATE_SETTINGS'.
    
    If the list exists, it will be assumes that each item in the list is the 
    name of a defined setting.  This setting (key and value) is then appended
    to a dict, that is returned in to the RequestContext for use in templates.
    
    Care should be taken not to add any database or other 'private' settings
    in to the list, as potentially it will be visable in templates.
    """
    
    settings_dict = settings.__dict__
    availible_settings = settings_dict.get('TEMPLATE_SETTINGS', [])
    template_settings = {}
    for setting in availible_settings:
        if setting in settings_dict:
            template_settings[setting] = settings_dict[setting]
    return {'settings' : template_settings}

def site_messages(request):
    message = Message.objects.get_active_message(datetime.datetime.now())
    return {'site_message': mark_safe(message.text)}
