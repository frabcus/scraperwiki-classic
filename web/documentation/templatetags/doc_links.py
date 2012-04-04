#!/usr/bin/env python

from django import template
register = template.Library()

from documentation.titles import page_titles

@register.simple_tag
def doc_link_full(template_name, language, title = None, text = None):
    template_name = template_name.replace('LANG', language)
    if not text:
        text = page_titles[template_name][0]
    if title:
        return '''<a href="/docs/%s/%s" title="%s">%s</a>''' % (language, template_name, title, text)
    else:
        return '''<a href="/docs/%s/%s">%s</a>''' % (language, template_name, text)

@register.simple_tag
def doc_link_toc(template_name, language, description = None, text = None):
    template_name = template_name.replace('LANG', language)
    text = text or page_titles[template_name][0]
    html = '''<dt><a href="/docs/%s/%s">%s</a></dt>''' % (language, template_name, text)
    if description:
        html += '''<dd><a href="/docs/%s/%s">%s</a></dd>''' % (language, template_name, description)
    return html

@register.simple_tag
def doc_change_lang(request, from_lang, to_lang):
    return request.path.replace(from_lang, to_lang)




