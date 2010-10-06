from django.template import Library, Node
from django.template.defaultfilters import stringfilter
import settings

import re
register = Library()

@register.inclusion_tag('codewiki/templatetags/screenshot.html')
def screen_shot(code_object, size='medium'):
    return {
        'url': settings.MEDIA_URL + 'screenshots/medium/' + code_object.get_screenshot_filename(size=size),
        'title': code_object.title,    
    }

