import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import datetime


class Command(BaseCommand):
    help = 'Email a report on the number of users and scrapers'
    
    def handle(self, **options):   
        
        total_users = User.objects.filter(is_active=False, is_staff=False, is_superuser=False).count()
        new_users_this_month = User.objects.filter(is_active=False, is_staff=False, is_superuser=False,date_joined__range=(datetime.datetime.now(), datetime.datetime.now() - datetime.timedelta(months=1))).count()

        print new_users_this_month