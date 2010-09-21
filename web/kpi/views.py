from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from codewiki.models import Scraper, Code
import datetime, calendar

from codewiki.management.commands.run_scrapers import GetUMLrunningstatus
from django.core.exceptions import ObjectDoesNotExist


# this clearly is something that should be implemented as a scraperwiki view

from pygooglechart import StackedVerticalBarChart

START_YEAR = 2010

def one_month_in_the_future(month, year):
    if month == 12:
        new_month = 1
    else:
        new_month = month + 1
    return datetime.date(year + (month / 12), new_month, 1)

def generate_chart_urls(years_list):
    total_scrapers = []
    new_scrapers = []
    total_users = []
    new_users = []
    for year in years_list:
        for month in year['months']:
            total_scrapers.append(month['total_scrapers'])
            new_scrapers.append(month['this_months_scrapers'])
            total_users.append(month['total_users'])
            new_users.append(month['this_months_users'])

    chart = StackedVerticalBarChart(((30 * len(total_scrapers)) + 100), 125, y_range=(0, sorted(total_scrapers + total_users)[-1]))
    chart.set_colours(['4d89f9', 'c6d9fd'])
    chart.set_bar_width(20)
    chart.set_legend(['Total Scrapers', 'Total Users'])
    chart.add_data(total_scrapers)
    chart.add_data(total_users)
    total_url = chart.get_url()

    chart = StackedVerticalBarChart(((30 * len(new_scrapers)) + 100), 125, y_range=(0, sorted(new_scrapers + new_users)[-1]))
    chart.set_colours(['4d89f9', 'c6d9fd'])
    chart.set_bar_width(20)
    chart.set_legend(['New Scrapers', 'New Users'])
    chart.add_data(new_scrapers)
    chart.add_data(new_users)
    new_url = chart.get_url()

    return total_url, new_url

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
        context['total_chart_url'], context['new_chart_url'] = generate_chart_urls(years_list)
        
        return render_to_response('kpi/index.html', context)
    else:
        raise PermissionDenied
    
def umlstatus(request):
    user = request.user
    if not user.is_staff:
        raise PermissionDenied
            
    statusscrapers = GetUMLrunningstatus()
    for status in statusscrapers:
        if status['scraperID']:
            status['scraper'] = Code.objects.get(guid=status['scraperID'])   # could throw ObjectDoesNotExist
        
    context = { 'statusscrapers': statusscrapers }
    return render_to_response('kpi/umlstatus.html', context)

