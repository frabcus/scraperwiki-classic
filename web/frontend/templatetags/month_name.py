from django.template import Library
import calendar

register = Library()

@register.simple_tag
def month_name(number):
    try:
        num = int(number)
        return calendar.month_name[num]
    except:
        return ""
