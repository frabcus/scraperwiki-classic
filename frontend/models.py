from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    """
	    This model holds the additional fields to be associated with a user in the system
        
        the alerts_last_sent and alert_frequency field hold when a notification email was last sent to this user
        and the frequency of these messages(in seconds) as requested by the user.
        
        Note, where any other model wishes to link to a user or reference a user, they should link to the
        user profile (this class), rather than directly to the user. this ensures that if we wish to change
        the definition of user, we only have to alter the UserProfile class to have everything continue to work
        instead of refactoring every place that connects to a resource/class outside of this application.
    """
    user             = models.ForeignKey(User, unique=True)
    email_address    = models.EmailField()
    bio              = models.TextField()
    created_at       = models.DateTimeField(auto_now_add = True)
    alerts_last_sent = models.DateTimeField()
    alert_frequency  = models.IntegerField()


# models related to user roles

class UserToUserRole(models.Model):
    """
        PRM: I did not want to have many different ways of connecting one user to another, so
        this class embodies any and all connections from one user to another. Following, etc.
	"""
    from_user_profile = models.ForeignKey(UserProfile, related_name = 'from_user')
    to_user_profile   = models.ForeignKey(UserProfile, related_name = 'to_user')
    role              = models.CharField(max_length = 100)
