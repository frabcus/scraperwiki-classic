from django.db import models
from django.contrib.auth.models import User

class Solicitation(models.Model):

    """
	   Requests for scrapers to be written. 
    """

    title   = models.CharField(max_length = 100, null=False, blank=False)
    details = models.TextField(null=False, blank=False)
    link    = models.URLField(verify_exists=True, max_length=200, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add = True)
    deleted = models.BooleanField()
    status  = models.CharField(max_length = 10)
    user_created = models.ForeignKey(User)