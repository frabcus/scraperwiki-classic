from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from scraper.models import Scraper
import datetime, calendar, itertools

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

    if user.is_authenticated() and user.is_superuser:
        years_list = []
        for year in range(START_YEAR, datetime.date.today().year + 1):
            months_list = []
            for month in range(1, 13):
                month_data = {}
                month_data['month'] = calendar.month_name[month]
                next_month = one_month_in_the_future(month, year) 
                month_data['total_scrapers'] = Scraper.objects.filter(first_published_at__lte=next_month).count()
                month_data['this_months_scrapers'] = Scraper.objects.filter(first_published_at__year=year, first_published_at__month=month).count()
                month_data['total_users'] = User.objects.filter(date_joined__lte=next_month).count()
                month_data['this_months_users'] = User.objects.filter(date_joined__year=year, date_joined__month=month).count()
                months_list.append(month_data)

                if next_month > datetime.date.today():
                    # There shouldn't be any data for the future!
                    break
            years_list.append({'year': year, 'months': months_list})

        context['data'] = years_list 
        
        return render_to_response('kpi/index.html', context)
    else:
        raise PermissionDenied
