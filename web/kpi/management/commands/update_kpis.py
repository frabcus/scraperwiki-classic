from django.core.management.base import BaseCommand
from kpi.models import DatastoreRecordCount
import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        DatastoreRecordCount.objects.create(date=datetime.date.today(),
                                            record_count=0)
