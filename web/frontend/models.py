from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    """
    This model holds the additional fields to be associated with a user in the
    system
    
    The alerts_last_sent and alert_frequency field hold when a notification
    email was last sent to this user and the frequency of these messages(in
    seconds) as requested by the user.
    
    Note, where any other model wishes to link to a user or reference a user,
    they should link to the user profile (this class), rather than directly to
    the user. this ensures that if we wish to change the definition of user,
    we only have to alter the UserProfile class to have everything continue to
    work instead of refactoring every place that connects to a resource/class
    outside of this application.
    """
    user             = models.ForeignKey(User, unique=True)
    bio              = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add = True)
    alerts_last_sent = models.DateTimeField(auto_now_add = True)
    alert_frequency  = models.IntegerField(null=True, blank=True)

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)        
        
class UserAlersTypes(models.Model):
    """
    
    """
    user = models.ForeignKey(User)
    message_type = models.CharField(blank=True, max_length=100)
    
# models related to user roles

class UserRoleManager(models.Manager):
    """
        This manager is used to decorate the collection objects on the user model
        so as to fascilitate the easy managing of user to user relationships.    
    """
    use_for_related_fields = True
    
    def following(self):
        return [role.to_user for role in self.get_query_set().filter(role='follow')]
        
    def followed_by(self):
        return [role.from_user for role in self.get_query_set().filter(role='follow')]
    
    def not_following_anyone(self):
        return len(self.following()) == 0
        
    def not_followed_by_anyone(self):
        return len(self.followed_by()) == 0
    

class UserToUserRole(models.Model):
    """
        PRM: I did not want to have many different ways of connecting one user to another, so
        this class embodies any and all connections from one user to another. Following, etc.
	"""
	
    objects = UserRoleManager()
    
    from_user = models.ForeignKey(User, related_name = 'to_user')
    to_user   = models.ForeignKey(User, related_name = 'from_user')
    role      = models.CharField(max_length = 100)

# Signal Registrations

# when a user gets registered, we want to generate a profile for them
from registration.signals import user_registered

def create_user_profile(sender, **kwargs):
    user = kwargs['user']
    profile = UserProfile(user = user, alert_frequency = 60*60*24)
    profile.save()

user_registered.connect(create_user_profile)
