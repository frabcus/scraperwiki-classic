from django.db import models

class DatastoreRecordCount(models.Model):
    date = models.DateField()
    record_count = models.IntegerField()

    def __unicode__(self):
        return u"%s - %d records" % (self.date, self.record_count)

class MonthlyCounts(models.Model):
    date = models.DateField() # first of the month

    total_scrapers = models.IntegerField()
    this_months_scrapers = models.IntegerField()

    total_views = models.IntegerField()
    this_months_views = models.IntegerField()

    total_users = models.IntegerField()
    this_months_users = models.IntegerField()

    active_coders = models.IntegerField()
    delta_active_coders = models.IntegerField()


