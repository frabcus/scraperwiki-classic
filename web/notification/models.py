from django.db import models
from django.contrib.auth.models import User

# models to implement the alert/notification system.
# this enables the system to arbitrarily send alerts/notifications to users and have these sent to the user
# via email no more frequently than they have requested.

class Notifications(object):
    """
        Class to hold the business logic to attempt to send notifications
    """
    pass

class AlertType(models.Model):
    """
        Items of this class define the different classifications of types of alert which can be sent.
        They are enumerated here so that the system does not need to have them hardcoded, and we can maintain
        them as we see fit.
    """
	
    code        = models.CharField(max_length = 10)
    description = models.TextField()
	

class AlertNotification(models.Model):
    """
        Users define which alerts they are happy to receive, they do this by checking a check box against the
        alert type in their profile. Checking the box will instantiate an object of this class, connected
        to the appropriate alert_type and the user_profile.
    """
    alert_type = models.ForeignKey(AlertType)
    user       = models.ForeignKey(User)

class AlertInstance(models.Model):
    """
        This embodies the record of a particular message of a type being sent to a user.
    """
    alert_type   = models.ForeignKey(AlertType)
    user         = models.ForeignKey(User)
    message      = models.CharField(max_length = 140)
    sent         = models.BooleanField()


