# encoding: utf-8
import datetime
import time

from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin

import managers.scraper
from django.db.models.signals import post_save
from registration.signals import user_registered

import tagging

import template
import util
import vc

from django.core.mail import send_mail

# models defining scrapers and their metadata.


class Scraper(models.Model):
    """
        A 'Scraper' is the definition of all versions of a particular scraper
        that are classed as being the same, though changed over time as the data required changes
        and the page being scraped changes, thus breaking a particular version.

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
    title             = models.CharField(max_length = 100, null=False, blank=False, verbose_name='Scraper Title', default='Untitled Scraper')
    short_name        = models.CharField(max_length = 50)
    source            = models.CharField(max_length = 100, blank=True)
    last_run          = models.DateTimeField(blank = True, null=True)
    description       = models.TextField(blank=True)
    license           = models.CharField(max_length = 100, blank=True)
    revision          = models.CharField(max_length = 100, null=True)
    created_at        = models.DateTimeField(auto_now_add = True)
    disabled          = models.BooleanField()
    deleted           = models.BooleanField()
    status            = models.CharField(max_length = 10)
    users             = models.ManyToManyField(User, through='UserScraperRole')
    guid              = models.CharField(max_length = 1000)
    published         = models.BooleanField(default=False)
    first_published_at   = models.DateTimeField(null=True)
    objects = managers.scraper.ScraperManager()
      
    def __unicode__(self):
      return self.short_name
    
    def save(self, commit=False, message=None, user=None):
      """
      this function saves the uninitialized and undeclared .code member of the object to the disk
      you just have to know it's there by looking into the cryptically named vc.py module
      """
      
      # if the scraper doesn't exist already give it a short name (slug)
      if self.short_name:
        self.short_name = util.SlugifyUniquely(self.short_name, Scraper, slugfield='short_name', instance=self)
      else:
        self.short_name = util.SlugifyUniquely(self.title, Scraper, slugfield='short_name', instance=self)
      
      if self.created_at == None:
          self.created_at = datetime.datetime.today()
                  
      if not self.guid:
          import hashlib
          guid = hashlib.md5("%s" % ("**@@@".join([self.short_name, str(time.mktime(self.created_at.timetuple())) ]))).hexdigest()
          self.guid = guid
      
      if self.__dict__.get('code'):
          vc.save(self)
          if commit:
            # Publish the scraper & set it's publish date
            self.published = True
            if self.first_published_at == None:
                self.first_published_at = datetime.datetime.today()
            vc.commit(self, message=message, user=user)
      super(Scraper, self).save()
    
    def language(self):
	    return "Python"
	
    def record_count(self):
      return Scraper.objects.item_count(self.guid)

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
      u = UserScraperRole(user=user, scraper=self, role=role)
      u.user = user
      u.save()

    def unfollow(self, user):
      """
      Deliberately not making this generic, as you can't stop being an owner or editor
      """
      UserScraperRole.objects.filter(scraper=self, user=user, role='follow').delete()
      return True
      
    def followers(self):
        return self.users.filter(userscraperrole__role='follow')

    def is_published(self):
	    return self.status == 'Published'
	    
    # currently, the only editor we have is the owner of the scraper.
    def editors(self):
        return (self.owner(),)
            
    def committed_code(self):
        code =  vc.get_code(self.short_name)
        return code

    def saved_code(self):
        code =  vc.get_code(self.short_name, committed=False)
        return code

    def number_of_lines(self):
        code = vc.get_code(self.short_name)
        return code.count("\n")
        
    def get_absolute_url(self):
        # used by RSS feeds - TODO
        return "/scrapers/%i/" % self.short_name

    def is_good(self):
        # don't know how goodness is going to be defined yet.
        return True

tagging.register(Scraper)
		
def post_Scraper_save_signal(sender, **kwargs):
  pass
post_save.connect(post_Scraper_save_signal, sender=Scraper)




class UserScraperRole(models.Model):
    """
        This embodies the roles associated between particular users and scrapers. This should be used
        to store all user/scraper relationships, ownership, editorship, whatever.
    """
    user    = models.ForeignKey(User)
    scraper = models.ForeignKey(Scraper)
    role    = models.CharField(max_length = 100)
    
    def __unicode__(self):
      return "Scraper_id: %s -> User: %s (%s)" % (self.scraper, self.user, self.role)
