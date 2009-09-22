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

# models defining scrapers and their metadata.
class Scraper(models.Model):
    """
        A 'Scraper' is the definition of all versions of a particular scraper
        that are classed as being the same, though changed over time as the data required changes
        and the page being scraped changes, thus breaking a particular version.
    """
    title             = models.CharField(max_length = 100)
    short_name        = models.CharField(max_length = 50)
    description       = models.TextField()
    license           = models.CharField(max_length = 100)
    created_at        = models.DateTimeField(auto_now_add = True)
    published_version = models.IntegerField()

class ScraperVersion(models.Model):
    """
        As a scraper is changed over time, it goes through multiple versions, it is still classed
        as being the same scraper.

        We are looking at holding the actual code of the scraper in mercurial, but it needs
        a counterpart in the database for relational reasons.

        Not sure what will form the linkage as yet (between here and mercurial).
        Possibly the version and or code and the scrapers shortname.
    """	
    scraper = models.ForeignKey(Scraper)
    version = models.IntegerField()
    code    = models.CharField(max_length = 100)

class ScraperInvocation(models.Model):
    """
        When a scraper is run, the record of that execution is captured as a 'ScraperInvocation'.
        This allows us to link the results of the scraping (debug output, actual data etc) back not only
        to a particular scraper, but to a particular version of the scraper.

        duration is in seconds and is a float field.
        published records whether this version of the scraper was the published version (run from the scheduler)
        or an 'in development' version, run from the frontend.

        PRM: There has been discussion as to whether this should be recorded in the database.
        I would prefer that it IS recorded in the database as that will ensure that all invocations of
        scrapers are handled and recorded in the same way. It reduces considerably the special purpose
        code that has to be written to treat different types of invocation in different ways.
    """
    scraper_version = models.ForeignKey(ScraperVersion)
    run_at          = models.DateTimeField()
    duration        = models.FloatField()
    log_text        = models.TextField()
    published       = models.BooleanField()
    status          = models.CharField(max_length = 10)

class ScraperException(models.Model):
    """
        If a scraper raises an exception while it is run, this fact is recorded here.
    """
    scraper_invocation = models.ForeignKey(ScraperInvocation)
    message            = models.CharField(max_length = 100)
    line_number        = models.IntegerField()
    backtrace          = models.TextField()

# models to define cached pages and to connect them to scraper invocations.
class CachedPage(models.Model):
    """
        This records the information used to request a page, along with the content that was retrieved
        and when this was done.

        PRM: Don't know whether content should be a TextField or an XmlField.
    """
    url          = models.URLField()
    method       = models.CharField(max_length = 1) # 'P' = Post, 'G' = Get.
    post_data    = models.CharField(max_length = 1000)
    cached_at    = models.DateTimeField(auto_now_add = True)
    time_to_live = models.IntegerField() # number of seconds after 'cached_at' for which this is fald
    content      = models.TextField()

class PageAccess(models.Model):
    """
       When a scraper requests a page, we check to see whether it is already alive in the cache, if it is
       we don't actually go get it, we used the cached version.

       But, the record of whether a page is used by a scraper is recorded as an object of this class, linking
       the ScraperInvocation with the cached page.
    """
    cached_page        = models.ForeignKey(CachedPage)
    scraper_invocation = models.ForeignKey(ScraperInvocation)

# models to implement the alert/notification system.
# this enables the system to arbitrarily send alerts/notifications to users and have these sent to the user
# via email no more frequently than they have requested.

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
    alert_type   = models.ForeignKey(AlertType)
    user_profile = models.ForeignKey(UserProfile)

class AlertInstance(models.Model):
    """
        This embodies the record of a particular message of a type being sent to a user.
    """
    alert_type   = models.ForeignKey(AlertType)
    user_profile = models.ForeignKey(UserProfile)
    message      = models.CharField(max_length = 140)
    sent         = models.BooleanField()

# models related to user roles

class UserToUserRole(models.Model):
    """
        PRM: I did not want to have many different ways of connecting one user to another, so
        this class embodies any and all connections from one user to another. Following, etc.
	"""
    from_user_profile = models.ForeignKey(UserProfile, related_name = 'from_user')
    to_user_profile   = models.ForeignKey(UserProfile, related_name = 'to_user')
    role              = models.CharField(max_length = 100)

class UserScraperRole(models.Model):
    """
        This embodies the roles associated between particular users and scrapers. This should be used
        to store all user/scraper relationships, ownership, editorship, whatever.
    """
    user_profile = models.ForeignKey(UserProfile)
    scraper      = models.ForeignKey(Scraper)
    role         = models.CharField(max_length = 100)

# Other models

class Comment(models.Model):
    """
        Currently, comments are flat, and can only be 'made on' scrapers.
    """
    author     = models.ForeignKey(UserProfile)
    scraper    = models.ForeignKey(Scraper)
    created_at = models.DateTimeField(auto_now_add = True)
    text       = models.TextField()