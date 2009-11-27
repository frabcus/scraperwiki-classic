import urllib, hashlib
from django import template
from django.http import HttpResponse
from django.conf import settings
from django.contrib.sites.models import Site

register = template.Library()

@register.inclusion_tag('frontend/templatetags/gravatar.html')

def show_gravatar(email, size=100, margintop=10):
    domain = Site.objects.get_current().domain
    default = domain + settings.MEDIA_URL + "/images/gravatar_default.png"
    url = "http://www.gravatar.com/avatar.php?"
    url += urllib.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(), 
        'default': default, 
        'size': str(size)
    })
    return {'gravatar': {'url': url, 'size': size, 'margintop': margintop}}
