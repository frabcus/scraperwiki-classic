from django.db import models

class ViewManager(models.Manager):
    
    def get_query_set(self):
        return super(ViewManager, self).get_query_set().filter(deleted=False)