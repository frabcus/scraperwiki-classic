import datetime

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.dispatch import dispatcher
from django.core.mail import send_mail, mail_admins
from django.conf import settings

from frontend import highrise

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
    scraper was run, saved, committed or when a comment has been added.
        
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
    object_id = models.PositiveIntegerField(blank=True, null=True)
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
    event_id = models.PositiveIntegerField(blank=True, null=True)
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
    beta_user        = models.BooleanField( default=False )
    
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

class MessageManager(models.Manager):
    def get_active_message(self, now):
        """
        The active message is the one that is displayed on the site.

        It is the most recently created message that isn't excluded
        because of its start or finish date.
        """
        messages = self.filter(Q(start__isnull=True) | Q(start__lte=now))
        messages = messages.filter(Q(finish__isnull=True) | Q(finish__gte=now))
        return messages.latest('id')

class Message(models.Model):
    text = models.TextField()
    start = models.DateTimeField(blank=True, null=True)
    finish = models.DateTimeField(blank=True, null=True)
    objects = MessageManager()

    def is_active_message(self):
        return Message.objects.get_active_message(datetime.datetime.now()) == self

    def __unicode__(self):
        if self.is_active_message():
            return "%s [Active]" % self.text
        else:
            return "%s [Inactive]" % self.text

class DataEnquiry(models.Model):
    date_of_enquiry = models.DateTimeField(auto_now_add=True)
    urls = models.TextField()
    columns = models.TextField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    telephone = models.CharField(max_length=32, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    visualisation = models.TextField(null=True, blank=True)
    application = models.TextField(null=True, blank=True)
    company_name = models.CharField(max_length=128, null=True, blank=True)
    broadcast = models.BooleanField()

    FREQUENCY_CHOICES = (
      ('once', 'Once only'),
      ('monthly', 'Monthly'),
      ('weekly', 'Weekly'),
      ('daily', 'Daily'),
      ('hourly', 'Hourly'),
      ('realtime', 'Real-time')
    )
    frequency = models.CharField(max_length=32, choices=FREQUENCY_CHOICES)

    CATEGORY_CHOICES = (
        ('private', 'private'),
        ('viz', 'viz'),
        ('app', 'app'),
        ('etl', 'etl'),
        ('public', 'public')
    )
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)

    class Meta:
        verbose_name_plural = "data enquiries"

    def __unicode__(self):
        return u"%s %s <%s>" % (self.first_name, self.last_name, self.email)

    def email_message(self):
        msg =  u"""
            Category: %s
            First Name: %s
            Last Name: %s
            Your email address: %s
            Your telephone number: %s
            Your company name: %s
            At which URL(s) can we find the data currently?: %s
            What information do you want scraped?: %s
            When do you need it by?: %s
            How often does the data need to be scraped?: %s
            What are your ETL needs?: %s
            What visualisation do you need?: %s
            What application do you want built?: %s
        """ % (self.category,
               self.first_name,
               self.last_name,
               self.email,
               self.telephone,
               self.company_name,
               self.urls,
               self.columns,
               self.due_date or '',
               self.frequency,
               self.description,
               self.visualisation,
               self.application)

        return msg.encode('utf-8')

def data_enquiry_post_save(sender, **kwargs):
    if kwargs['created']:
        
        if not hasattr(settings,'HIGHRISE_ENABLED') or settings.HIGHRISE_ENABLED == False:
            return
        
        instance = kwargs['instance']
        send_mail('Data Request', instance.email_message(), instance.email, [settings.FEEDBACK_EMAIL], fail_silently=False)

        if instance.category not in ['public']:
            try:
                h = highrise.HighRise(settings.HIGHRISE_PROJECT, settings.HIGHRISE_KEY)

                try:
                    requester = h.search_people_by_email(instance.email.encode('utf-8'))[0]
                except Exception,err:
                    # Removed indexerror to catch problems that seem to happen when we 
                    # can't find the user.                    
                    try:
                        requester = h.create_person(instance.first_name.encode('utf-8'),
                                                    instance.last_name.encode('utf-8'),
                                                    instance.email)
                        h.tag_person(requester.id, 'Lead')
                    except Exception, e2:
                        mail_admins('HighRise failed to find/create user with errors', str(err) + ',' + str(e2))                    
                        return

                h.create_note_for_person(instance.email_message(), requester.id)

                cat = h.get_task_category_by_name('To Do')

                task_owner = h.get_user_by_email(settings.HIGHRISE_ASSIGN_TASK_TO)

                # Split out so we can tell which one is causing the problems
                rid = requester.id
                cid = cat.id
                tid = task_owner.id
                
                h.create_task_for_person('Data Request Followup', tid, cid, rid)
            except highrise.HighRiseException, ex:
                msg = "%s\n\n%s" % (ex.message, instance.email_message())
                mail_admins('HighRise update failed', msg)
            except AttributeError, eAttr:
                # We expect this from create_task_for_person with missing data.
                msg = "%s\n\n%s" % (str(eAttr), instance.email_message())
                mail_admins('HighRise update failed', msg)
            

post_save.connect(data_enquiry_post_save, sender=DataEnquiry)
