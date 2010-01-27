import time
import datetime

from django.db import models
from django.contrib.auth.models import User
import settings

class api_key(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(blank=True, max_length=32)
    active = models.BooleanField(default=True)
    description = models.TextField(null=False, blank=False)
    
    def __unicode__(self):
      return "%s" % self.key
    
    def save(self):
        if not self.key:
            import hashlib
            unique_string = "**@@@".join([
                settings.SECRET_KEY, 
                str(self.user.id), 
                str(datetime.datetime.today())])
            
            key = hashlib.md5("%s" % unique_string).hexdigest()
            self.key = key[:32]


        super(api_key, self).save()