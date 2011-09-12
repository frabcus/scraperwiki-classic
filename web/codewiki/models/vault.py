from django.db import models
from django.contrib.auth.models import User

PLAN_TYPES = (
    ('individual', 'Individual'),
    ('corporate', 'Corporate'),    
)

# One instance per user that has a premium account.
class Vault(models.Model):
    user = models.OneToOneField(User, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.CharField(max_length=32, choices=PLAN_TYPES)    

    def __unicode__(self):
        return "%s vault created on %s" % (self.plan, self.created_at)

    class Meta:
        app_label = 'codewiki'


