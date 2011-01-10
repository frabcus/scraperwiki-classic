from django.db import models

class DatastoreRecordCount(models.Model):
    date = models.DateField()
    record_count = models.IntegerField()

    def __unicode__(self):
        return u"%s - %d records" % (self.date, self.record_count)
