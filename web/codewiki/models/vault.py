from django.db import models
from django.contrib.auth.models import User

# One instance per user that has a premium account.
class Vault(models.Model):
    user = models.OneToOneField(User, primary_key=True)

    class Meta:
        app_label = 'codewiki'


