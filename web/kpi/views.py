from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.template import RequestContext

from codewiki.models import Scraper, Code, View
import datetime, calendar

START_YEAR = 2010

def one_month_in_the_future(month, year):
    if month == 12:
        new_month = 1
    else:
        new_month = month + 1
    return datetime.date(year + (month / 12), new_month, 1)

def index(request):
    user = request.user
    context = {}

    if not user.is_authenticated() or not user.is_superuser:
        raise PermissionDenied

    years_list = []

    for i, year in enumerate(range(START_YEAR, datetime.date.today().year + 1)):
        months_list = []
        for month in range(1, 13):
            month_data = {}
            month_data['month'] = calendar.month_abbr[month]
            next_month = one_month_in_the_future(month, year) 
            month_data['total_scrapers'] = Scraper.objects.filter(first_published_at__lte=next_month).exclude(privacy_status="deleted").count()
            month_data['this_months_scrapers'] = Scraper.objects.filter(first_published_at__year=year, first_published_at__month=month).exclude(privacy_status="deleted").count()
            month_data['total_views'] = View.objects.filter(first_published_at__lte=next_month).exclude(privacy_status="deleted").count()
            month_data['this_months_views'] = View.objects.filter(first_published_at__year=year, first_published_at__month=month).exclude(privacy_status="deleted").count()
            month_data['total_users'] = User.objects.filter(date_joined__lte=next_month).count()
            month_data['this_months_users'] = User.objects.filter(date_joined__year=year, date_joined__month=month).count()
            months_list.append(month_data)

            if next_month > datetime.date.today():
                # There shouldn't be any data for the future!
                break
        years_list.append({'year': year, 'months': months_list, 'offset': i * 12})
   
    # work out unique active code writers / month ..
    for code in Code.objects.all():
        for commitentry in code.get_commit_log():
            # don't count editing own emailer for now
            if code.is_emailer():
                continue

            user = commitentry['user']
            when = commitentry['date']

            username = user.username
            year = when.year

            month_data = years_list[year - START_YEAR]['months'][when.month - 1]
            if 'active_coders' not in month_data.keys():
                month_data['active_coders'] = {}
            month_data['active_coders'][username] = 1
    # ... and count how many entries there are
    last_active_coders = 0
    for i, year in enumerate(range(START_YEAR, datetime.date.today().year + 1)):
        for month in range(1, 13):
            month_data = years_list[i]['months'][month - 1]
            if 'active_coders' not in month_data.keys():
                month_data['active_coders'] = 0
            else:
                month_data['active_coders'] = len(month_data['active_coders'])

            month_data['delta_active_coders'] = month_data['active_coders'] - last_active_coders
            last_active_coders = month_data['active_coders']
            
            next_month = one_month_in_the_future(month, year) 
            if next_month > datetime.date.today():
                break

    context['data'] = years_list 
    
    return render_to_response('kpi/index.html', context, context_instance = RequestContext(request))
    
