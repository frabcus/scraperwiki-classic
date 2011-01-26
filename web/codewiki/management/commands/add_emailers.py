from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from codewiki.models import Scraper

import random
import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            if not Scraper.objects.get_emailer_for_user(user):
                last_run = datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 24))
                Scraper.objects.create_emailer_for_user(user, last_run)
                print "Added emailer for %s" % user.username
            else:
                print "%s already has an emailer" % user.username
