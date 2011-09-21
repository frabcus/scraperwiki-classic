from django.db import models
from django.contrib.auth.models import User

PLAN_TYPES = (
    ('individual', 'Individual'),
    ('corporate', 'Corporate'),    
)

# One instance per user that has a premium account. 
# If we now use userinstance.vault we are likely to get
# an error so we'll need to  wrap each call in a 
# Vault.DoesNotExist exception check instead. Have
# implemented a static check here to do that and save a 
# couple of lines
class Vault(models.Model):
    user = models.OneToOneField(User, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.CharField(max_length=32, choices=PLAN_TYPES)    

    # A list of the members who can access this vault.  This is 
    # distinct from the own (self.user) of the vault.
    members = models.ManyToManyField(User, related_name='vaults')

    @staticmethod
    def for_user( user ):
        try:
            return user.vault
        except Vault.DoesNotExist:
            return None

    def __unicode__(self):
        return "%s vault created on %s" % (self.plan, self.created_at)

    class Meta:
        app_label = 'codewiki'


