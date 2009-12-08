import urllib, hashlib
from django import template
from django.http import HttpResponse

register = template.Library()

@register.inclusion_tag('frontend/templatetags/gravatar.html')

def show_gravatar(email, size="medium", margintop=10):
    default = "/media/images/gravatar_default.png"
    url = "http://www.gravatar.com/avatar.php?"
    dimensions = 30
    if (size == "large"):
       dimensions = 100
    elif (size == "small"):
       dimensions = 10
    url += urllib.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(), 
        'default': default, 
        'size': str(dimensions)
    })
    return {'gravatar': {'url': url, 'size': dimensions, 'margintop': margintop}}
