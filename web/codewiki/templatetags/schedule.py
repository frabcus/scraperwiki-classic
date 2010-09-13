from django.template import Library, Node
from django.template.defaultfilters import stringfilter
from codewiki.models.scraper import SCHEDULE_OPTIONS

register = Library()

@stringfilter
def schedule(value):
    result = 'Error'
    for schedule_option in SCHEDULE_OPTIONS:
        if schedule_option[0] == int(value):
            result = schedule_option[1]
    return result

register.filter(schedule)