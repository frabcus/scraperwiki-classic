from django.template import Library, Node
from django.template.defaultfilters import stringfilter

import re
register = Library()

@stringfilter
def replace(val):
    return re.sub('_|-',' ',val)

register.filter(replace)
