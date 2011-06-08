from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.template import RequestContext

from codewiki.models import Scraper, Code, View

import datetime, calendar

def index(request):
    user = request.user
    context = {}

    if not user.is_authenticated() or not user.is_superuser:
        raise PermissionDenied

    #month_data['month'] = calendar.month_abbr[month]
    #years_list[-1]['months'][-1]['current_month'] = True
    #years_list.append({'year': year, 'months': months_list, 'offset': i * 12})

    context['data'] = years_list 
    
    return render_to_response('kpi/index.html', context, context_instance = RequestContext(request))
    
