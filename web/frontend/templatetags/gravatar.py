import urllib, hashlib
from django import template
from django.http import HttpResponse
from django.conf import settings
from django.contrib.sites.models import Site

register = template.Library()

@register.inclusion_tag('frontend/templatetags/gravatar.html')

def show_gravatar(user, size = 'medium'):

    #work out size
    size_px = 0
    if size == 'small':
        size_px = 20
    elif size == 'medium':
        size_px = 40
    elif size == 'large':
        size_px = 125

    domain = Site.objects.get_current().domain
    default = domain + settings.MEDIA_URL + "/images/gravatar_default.png"
    url = "http://www.gravatar.com/avatar.php?"
    url += urllib.urlencode({
        'gravatar_id': hashlib.md5(user.email).hexdigest(), 
        'default': default, 
        'size': str(size_px)
    })
    return {'gravatar': {'url': url, 'size': size, 'size_px': size_px, 'username': user.username}}