import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class AlertTypes(models.Model):
    """
    Model defining what type of alerts a user will get.
    
    `name`
        should match the 'message_type' in codewiki.models.ScraperHistory
    `label`
        is the default text to be displaied on the user profile form. This may
        not be the best way of doing it, but it does make sure the form
        options are correct.
    `applies_to`
        is for allowing users to get alerts from the history table for
        different types of scrapers. For example, we want to distinguish
        between alerts for scrapers one owns and scrapers one 'watches' (when
        that feature is availible). By default there is no distinction between
        'owning' and 'contributing'.
    """
    content_type = models.ForeignKey(ContentType)
    name = models.CharField(blank=True, 
                            max_length=100, 
                            unique=True)
    label = models.CharField(blank=True, max_length=500)
    applies_to = models.CharField(blank=False, max_length=100)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Alert Types"
        verbose_name = "Alert Type"
        ordering = ['content_type']

class Alerts(models.Model):
    """
    Stores 'alerts' for an object. Alerts can be anything, such as when a
    scraper was run, saved, committed or when a comment has been added to the
    market place.
        
    'message_type' is for storing diferent types of message.  
    
    Suggected conventions are:
        * 'run_success'
        * 'run_fail'
        * 'commit'
        
    """
    
    # there are two GenericForeignKey entries in this class that cause massive 
    # complications in order to avoid the evil of including fields in the base class that are 
    # not applicable to all types.
    # could be worse; could use inherited classes
    
    # the object about which the alert is about, eg codewiki.models.Code or User, 
    # notwithstanding the fact that there is a user field already below
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveSmallIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    # assumes this represents the actual type of the alert (although you will have to dig into the special kind of alert to represent it properly in ways not covered by message_value)
    message_type = models.CharField(blank=False, max_length=100)  
    message_value = models.CharField(blank=True, null=True, max_length=5000)
    
    meta = models.CharField(blank=True, max_length=1000)
    message_level = models.IntegerField(blank=True, null=True, default=0)
    datetime = models.DateTimeField(blank=False, default=datetime.datetime.now)
    user = models.ForeignKey(User, blank=True, null=True)
    historicalgroup = models.CharField(blank=True, max_length=100)  # currently this is set from earliesteditor

    # links to the object with further event information (either codewiki.models.Code.CodeCommitEvent or codewiki.models.Scraper.ScraperRunEvent)
    event_type = models.ForeignKey(ContentType, null=True, related_name='event_alerts_set')
    event_id = models.PositiveSmallIntegerField(blank=True, null=True)
    event_object = generic.GenericForeignKey('event_type', 'event_id')


    objects = models.Manager()
    
    def __unicode__(self):
        return "%s: '%s', message: %s" % \
                            (self.content_type, 
                            self.content_object,
                            self.message_type,)

    class Meta:
        verbose_name_plural = "Alerts"
        verbose_name = "Alert"

    def __str__(self):
        return str(self.__unicode__())

    class Meta:
        ordering = ('-datetime',)


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
    name             = models.CharField(max_length=64)
    bio              = models.TextField(blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    alerts_last_sent = models.DateTimeField(auto_now_add=True)
    alert_frequency  = models.IntegerField(null=True, blank=True)
    alert_types      = models.ManyToManyField(AlertTypes)
    
    objects = models.Manager()
    

    def save(self):
        new = False
        if not self.pk:
            new = True
        
        #do the parent save
        super(UserProfile, self).save()
        
        if new:
            # This is a new object
            # Create some default alerts.
            # By default, all alerts relating to scrapers are activated.
            default_alerts = AlertTypes.objects.all()
            self.alert_types = default_alerts
            #do the parent save again, now with default alerts
            super(UserProfile, self).save()
            
    
    def __unicode__(self):
        return unicode(self.user)

    class Meta:
        ordering = ('-created_at',)
    
    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)        
        

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
    
    from_user = models.ForeignKey(User, related_name='to_user')
    to_user   = models.ForeignKey(User, related_name='from_user')
    role      = models.CharField(max_length = 100)

# Signal Registrations
# when a user is created, we want to generate a profile for them

def create_user_profile(sender, instance, created, **kwargs):
    if created and sender == User:
        try:
            profile = UserProfile(user=instance, alert_frequency=60*60*24)
            profile.save()
        except:
            # syncdb is saving the superuser
            # UserProfile is yet to be created by migrations
            pass

models.signals.post_save.connect(create_user_profile)
