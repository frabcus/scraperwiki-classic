from django.db import models
from django.contrib.auth.models import User

PLAN_TYPES = (
    ('individual', 'Individual'),
    ('corporate', 'Corporate'),    
)

# One instance per user that has a premium account. 
# TODO: Constrain this so each user can only have one.
class Vault(models.Model):
    user = models.OneToOneField(User)

    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.CharField(max_length=32, choices=PLAN_TYPES)    

    # A list of the members who can access this vault.  This is 
    # distinct from the owner (self.user) of the vault.
    members = models.ManyToManyField(User, related_name='vaults')

    def __unicode__(self):
        return "%s' %s vault created on %s" % (self.user.username, self.plan, self.created_at)

    class Meta:
        app_label = 'codewiki'


