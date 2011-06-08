from django.core.management.base import BaseCommand
from django.db.models import Sum

from kpi.models import DatastoreRecordCount, MonthlyCounts
from codewiki.models import Scraper, Code

import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        # count records in database
        record_count_now = Scraper.objects.aggregate(record_count=Sum('record_count'))['record_count']
        drc = DatastoreRecordCount.objects.get_or_create(date=datetime.date.today(), defaults = {'record_count':  record_count_now})[0]
        drc.record_count = record_count_now
        drc.save()

