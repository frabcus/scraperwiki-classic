#!/usr/bin/env python

from django import template
register = template.Library()

@register.simple_tag
def body_class(request):
    if request.path == '/':
        return 'class="frontpage"'
    else:
        return 'class="%s"' % ' '.join(request.path[1:].split('/'))
