# encoding: utf-8
import datetime
import time

from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
import settings

import managers.scraper
from django.db.models.signals import post_save
from registration.signals import user_registered

import tagging
from frontend import models as frontendmodels

import util
import vc

try:
    import json
except:
    import simplejson as json

from django.core.mail import send_mail

# models defining scrapers and their metadata.

LANGUAGES = (
    ('Python', 'Python'),
    ('PHP', 'PHP'),
#    ('Ruby', 'Ruby'),
)

class Scraper(models.Model):
    """
        A 'Scraper' is the definition of all versions of a particular scraper
        that are classed as being the same, though changed over time as the
        data required changes and the page being scraped changes, thus
        breaking a particular version.
        
         scrapers are related to users through the UserScraperRole table.
        
         you can get the owner of a scraper by....
        
         scraper.owner()
        
         or the people following this scraper...
        
         scraper.followers()
        
         from the user side, you can find a users scraper with
        
         user.scraper_set.owned()
        
         or, the scrapers a user is following by....
        
         user.scraper_set.watching()

    """
    title             = models.CharField(max_length=100, 
                                        null=False, 
                                        blank=False, 
                                        verbose_name='Scraper Title', 
                                        default='Untitled Scraper')
    short_name        = models.CharField(max_length=50)
    source            = models.CharField(max_length=100, blank=True)
    last_run          = models.DateTimeField(blank=True, null=True)
    description       = models.TextField(blank=True)
    license           = models.CharField(max_length=100, blank=True)
    revision          = models.CharField(max_length=100, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    disabled          = models.BooleanField()
    deleted           = models.BooleanField()
    status            = models.CharField(max_length=10, blank=True)
    users             = models.ManyToManyField(User, through='UserScraperRole')
    guid              = models.CharField(max_length=1000)
    published         = models.BooleanField(default=False)
    first_published_at   = models.DateTimeField(null=True, blank=True)
    featured          = models.BooleanField(default=False)
    line_count        = models.IntegerField(default=0)
    record_count      = models.IntegerField(default=0)
    has_geo           = models.BooleanField(default=False)
    has_temporal      = models.BooleanField(default=False)
    scraper_sparkline_csv     = models.CharField(max_length=255, null=True)
    run_interval      = models.IntegerField(default=86400)   # to go

    istutorial        = models.BooleanField(default=False)
    isstartup         = models.BooleanField(default=False)
    
    language          = models.CharField(max_length=32, choices=LANGUAGES, default='Python')

    objects = managers.scraper.ScraperManager()
    unfiltered = models.Manager()

    def __unicode__(self):
        return self.short_name
    
    def buildfromfirsttitle(self):
        assert not self.short_name and not self.guid
        import hashlib
        self.short_name = util.SlugifyUniquely(self.title, Scraper, slugfield='short_name', instance=self)
        self.created_at = datetime.datetime.today()  # perhaps this should be moved out to the draft scraper
        self.guid = hashlib.md5("%s" % ("**@@@".join([self.short_name, str(time.mktime(self.created_at.timetuple()))]))).hexdigest()
     
  
    def count_records(self):
        return int(Scraper.objects.item_count(self.guid))

    def owner(self):
        if self.pk:
            owner = self.users.filter(userscraperrole__role='owner')
            if len(owner) >= 1:
                return owner[0]
        return None

    def contributors(self):
        if self.pk:
            contributors = self.users.filter(userscraperrole__role='editor')
        return contributors
    
    def followers(self):
        if self.pk:
            followers = self.users.filter(userscraperrole__role='follow')
        return followers

    def add_user_role(self, user, role='owner'):
        """
        Method to add a user as either an editor or an owner to a scraper.
  
        - `user`: a django.contrib.auth.User object
        - `role`: String, either 'owner' or 'editor'
        
        Valid role are:
          * "owner"
          * "editor"
          * "follow"
        
        """
  
        valid_roles = ['owner', 'editor', 'follow']
        if role not in valid_roles:
            raise ValueError("""
              %s is not a valid role.  Valid roles are:\n
              %s
              """ % (role, ", ".join(valid_roles)))
  
        #check if role exists before adding 
        u, created = UserScraperRole.objects.get_or_create(user=user, 
                                                           scraper=self, 
                                                           role=role)

    def unfollow(self, user):
        """
        Deliberately not making this generic, as you can't stop being an owner
        or editor
        """
        UserScraperRole.objects.filter(scraper=self, 
                                       user=user, 
                                       role='follow').delete()
        return True

    def followers(self):
        return self.users.filter(userscraperrole__role='follow')

    def is_published(self):
        return self.status == 'Published'

    # currently, the only editor we have is the owner of the scraper.
    def editors(self):
        return (self.owner(),)
            
    
    # this functions to go
    def saved_code(self):
        return vc.MercurialInterface().getstatus(self)["code"]

        
        
    @models.permalink
    def get_absolute_url(self):
        return ('scraper_overview', [self.short_name])

    def is_good(self):
        # don't know how goodness is going to be defined yet.
        return True

    # update scraper meta data (lines of code etc)    
    def update_meta(self):
        # if publishing for the first time set the first published date
        if self.published and self.first_published_at == None:
            self.first_published_at = datetime.datetime.today()
        
        #update line counts etc
        self.record_count = self.count_records()
        self.has_geo = bool(Scraper.objects.has_geo(self.guid))
        self.has_temporal = bool(Scraper.objects.has_temporal(self.guid))
        
        #get data for sparklines
        sparline_days = settings.SPARKLINE_MAX_DAYS
        created_difference = datetime.datetime.now() - self.created_at
        
        #if (created_difference.days < settings.SPARKLINE_MAX_DAYS):
        #    sparline_days = created_difference.days

        #minimum of 1 day
        recent_record_count = Scraper.objects.recent_record_count(self.guid, sparline_days)
        self.scraper_sparkline_csv = ",".join("%d" % count for count in recent_record_count)

    def content_type(self):
        return ContentType.objects.get(app_label="scraper", model="Scraper")

    def get_metadata(self, name, default=None):
        try:
            return json.loads(self.scrapermetadata_set.get(name=name).value)
        except:
            return default
        
        

#register tagging for scrapers
try:
    tagging.register(Scraper)
except tagging.AlreadyRegistered:
    pass
    
    
class UserScraperRole(models.Model):
    """
    This embodies the roles associated between particular users and scrapers.
    This should be used to store all user/scraper relationships, ownership,
    editorship, whatever.
    """
    user    = models.ForeignKey(User)
    scraper = models.ForeignKey(Scraper)
    role    = models.CharField(max_length=100)
    
    def __unicode__(self):
        return "Scraper_id: %s -> User: %s (%s)" % \
                                        (self.scraper, self.user, self.role)

class UserScraperEditing(models.Model):
    """
    Updated by Twisted to state which scrapers are being editing at this moment
    """
    user    = models.ForeignKey(User, null=True)
    scraper = models.ForeignKey(Scraper, null=True)
    editingsince = models.DateTimeField(blank=True, null=True)
    runningsince = models.DateTimeField(blank=True, null=True)
    closedsince  = models.DateTimeField(blank=True, null=True)
    twisterclientnumber = models.IntegerField(default=-1)
    twisterscraperpriority = models.IntegerField(default=0)   # >0 another client has priority on this scraper
    
        
    def __unicode__(self):
        return "Editing: Scraper_id: %s -> User: %s (%d)" % (self.scraper, self.user, self.twisterclientnumber)


class ScraperMetadata(models.Model):
    """
    Allows named metadata to be associated with a scraper
    """
    name = models.CharField(max_length=100, null=False, blank=False)
    scraper = models.ForeignKey(Scraper, null=False)
    run_id = models.CharField(max_length=100, null=False, blank=False)
    value = models.TextField()

    def __unicode__(self):
        return u"%s['%s']" % (self.scraper, self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('metadata_api', [self.scraper.guid, self.name])

    class Meta:
        verbose_name_plural = 'scraper metadata'

class ScraperRunEvent(models.Model):
    scraper = models.ForeignKey(Scraper)
    run_id = models.CharField(max_length=100)
    pid = models.IntegerField()
    run_started = models.DateTimeField()
    run_ended = models.DateTimeField(null=True)
    records_produced = models.IntegerField(default=0)
    pages_scraped = models.IntegerField(default=0)
    output = models.TextField()

    def __unicode__(self):
        return u'start: %s   end: %s' % (self.run_started, self.run_ended)

    @models.permalink
    def get_absolute_url(self):
        return ('run_event', [self.id])

class ScraperCommitEvent(models.Model):
    revision = models.IntegerField()

    def __unicode__(self):
        return unicode(self.revision)

    @models.permalink
    def get_absolute_url(self):
        return ('commit_event', [self.id])
