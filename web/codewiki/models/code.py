import datetime
import time
import os

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from codewiki.managers.code import CodeManager
import tagging
import hashlib

from codewiki import vc
from codewiki import util

try:
    import json
except:
    import simplejson as json

LANGUAGES_DICT = {
    'python' : 'Python',
    'php' : 'PHP',
    'ruby' : 'Ruby',

    'html' : 'HTML',
    'javascript' : 'Javascript',
    #'css' : 'CSS',
    #'wikicreole' : 'Wikicreole',
}
LANGUAGES = [ (k,v) for k,v in LANGUAGES_DICT.iteritems() ]

# used for new scraper/view dialogs
SCRAPER_LANGUAGES = [ (k, LANGUAGES_DICT[k]) for  k in ["python", "ruby", "php"] ]
VIEW_LANGUAGES = [ (k, LANGUAGES_DICT[k]) for  k in ["python", "ruby", "php", "html"] ]
HELP_LANGUAGES = [ (k, LANGUAGES_DICT[k]) for  k in ["python", "ruby", "php"] ]

WIKI_TYPES = (
    ('scraper', 'Scraper'),
    ('view', 'View'),    
)



class Code(models.Model):

    # model fields
    title              = models.CharField(max_length=100,
                                        null=False,
                                        blank=False,
                                        verbose_name='Scraper Title',
                                        default='Untitled')
    short_name         = models.CharField(max_length=50, unique=True)
    source             = models.CharField(max_length=100, blank=True)
    description        = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    deleted            = models.BooleanField()
    status             = models.CharField(max_length=10, blank=True, default='ok')
    users              = models.ManyToManyField(User, through='UserCodeRole')
    guid               = models.CharField(max_length=1000)
    published          = models.BooleanField(default=True)
    first_published_at = models.DateTimeField(null=True, blank=True)
    line_count         = models.IntegerField(default=0)    
    featured           = models.BooleanField(default=False)
    istutorial         = models.BooleanField(default=False)
    isstartup          = models.BooleanField(default=False)
    language           = models.CharField(max_length=32, choices=LANGUAGES,  default='Python')
    wiki_type          = models.CharField(max_length=32, choices=WIKI_TYPES, default='scraper')    
    relations          = models.ManyToManyField("self", blank=True)  # manage.py refuses to generate the tabel for this, so you haev to do it manually.
    forked_from        = models.ForeignKey('self', null=True, blank=True)
    
    # managers
    objects = CodeManager()
    unfiltered = models.Manager()

    def __init__(self, *args, **kwargs):
        super(Code, self).__init__(*args, **kwargs)
        if not self.created_at:
            self.created_at = datetime.datetime.today()  

    def save(self, *args, **kwargs):
        if self.published and self.first_published_at == None:
            self.first_published_at = datetime.datetime.today()

        if not self.short_name:
            self._buildfromfirsttitle()

        if not self.guid:
            self.set_guid()

        super(Code, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return self.short_name

    @property
    def vcs(self):
        if self.forked_from:
            return vc.MercurialInterface(self.get_repo_path(), self.forked_from.get_repo_path())
        else:
            return vc.MercurialInterface(self.get_repo_path())

    def commit_code(self, code_text, commit_message, user):
        self.vcs.savecode(code_text)
        rev = self.vcs.commit(message=commit_message, user=user)
        return rev

    def get_commit_log(self):
        return self.vcs.getcommitlog()

    def get_file_status(self):
        return self.vcs.getfilestatus()

    def get_vcs_status(self, revision = None):
        return self.vcs.getstatus(revision)

    def get_reversion(self, rev):
        return self.vcs.getreversion(rev)

    def _buildfromfirsttitle(self):
        assert not self.short_name
        self.short_name = util.SlugifyUniquely(self.title, Code, slugfield='short_name', instance=self)

    def set_guid(self):
        self.guid = hashlib.md5("%s" % ("**@@@".join([self.short_name, str(time.mktime(self.created_at.timetuple()))]))).hexdigest()
     
    def owner(self):
        if self.pk:
            owner = self.users.filter(usercoderole__role='owner')
            if len(owner) >= 1:
                return owner[0]
        return None

    def contributors(self):
        if self.pk:
            contributors = self.users.filter(usercoderole__role='editor')
        return contributors
    
    def followers(self):
        if self.pk:
            followers = self.users.filter(usercoderole__role='follow')
        return followers

    def emailers(self):
        if self.pk:
            emailers = self.users.filter(usercoderole__role='email')
        return emailers
        
    def requesters(self):
        if self.pk:
            requesters = self.users.filter(usercoderole__role='requester')
        return requesters        

    def add_user_role(self, user, role='owner'):
        """
        Method to add a user as either an editor or an owner to a scraper/view.
  
        - `user`: a django.contrib.auth.User object
        - `role`: String, either 'owner' or 'editor'
        
        Valid role are:
          * "owner"
          * "editor"
          * "follow"
          * "requester"
          * "email"
        
        """

        valid_roles = ['owner', 'editor', 'follow', 'requester', 'email']
        if role not in valid_roles:
            raise ValueError("""
              %s is not a valid role.  Valid roles are:\n
              %s
              """ % (role, ", ".join(valid_roles)))

        #check if role exists before adding 
        u, created = UserCodeRole.objects.get_or_create(user=user, 
                                                           code=self, 
                                                           role=role)

    def unfollow(self, user):
        """
        Deliberately not making this generic, as you can't stop being an owner
        or editor
        """
        UserCodeRole.objects.filter(code=self, 
                                    user=user, 
                                    role='follow').delete()
        return True

    def followers(self):
        return self.users.filter(usercoderole__role='follow')

    # currently, the only editor we have is the owner of the scraper.
    def editors(self):
        return (self.owner(),)

    def saved_code(self, revision = None):
        return self.get_vcs_status(revision)["code"]

    def get_repo_path(self):
        if settings.SPLITSCRAPERS_DIR:
            return os.path.join(settings.SPLITSCRAPERS_DIR, self.short_name)
        
        result = None
        if self.wiki_type == 'view':
            result = settings.VMODULES_DIR
        else:
            result = settings.SMODULES_DIR
        return result

    @models.permalink
    def get_absolute_url(self):
        return ('code_overview', [self.wiki_type, self.short_name])

    def is_good(self):
        # don't know how goodness is going to be defined yet.
        return True

    # update scraper meta data (lines of code etc)    
    def update_meta(self):
        pass

    # this is just to handle the general pointer put into Alerts
    def content_type(self):
        return ContentType.objects.get(app_label="codewiki", model="Code")

    def get_metadata(self, name, default=None):
        try:
            return json.loads(self.scrapermetadata_set.get(name=name).value)
        except:
            return default

    def get_screenshot_filename(self, size='medium'):
        return "%s.png" % self.short_name

    def get_screenshot_filepath(self, size='medium'):
        filename = self.get_screenshot_filename(size)
        return os.path.join(settings.SCREENSHOT_DIR, size, filename)

    def has_screenshot(self, size='medium'):
        return os.path.exists(self.get_screenshot_filepath(size))

    class Meta:
        app_label = 'codewiki'


            # all authorization to go through here
            # actions are overview, changeadmin, comments, history
    def actionauthorized(self, user, action):
        if self.deleted:
            return False
        if not user.is_authenticated() and action == "changeadmin":
            return False
        if not self.published and not user.is_authenticated():
            return False
        return True

    def authorizationfailedmessage(self, user, action):
        if self.deleted:
            return {'heading': 'Deleted', 'body': "Sorry this %s has been deleted" % self.wiki_type}
        if not user.is_authenticated() and action == "changeadmin":
            return {'heading': 'Not logged in', 'body': "only logged in users can change the settings"}
        if not self.published and not user.is_authenticated():
            return {'heading': 'Access denied', 'body': "not published and you are not logged in"}
        return {'heading': "unknown", "body":"unknown"}

    
    # tags have been unhelpfully attached to the scraper and view classes rather than the base code class
    # we can minimize the damage caused by this decision (in terms of forcing the scraper/view code to be 
    # unnecessarily separate by filtering as much of this application as possible through this interface
    def gettags(self):
        if self.wiki_type == "scraper":
            return tagging.models.Tag.objects.get_for_object(self.scraper)
        return tagging.models.Tag.objects.get_for_object(self.view)

    def settags(self, tag_names):
        if self.wiki_type == "scraper":
            tagging.models.Tag.objects.update_tags(self.scraper, tag_names)
        else:
            tagging.models.Tag.objects.update_tags(self.view, tag_names)



class UserCodeRole(models.Model):
    """
    This embodies the roles associated between particular users and scrapers/views.
    This should be used to store all user/code relationships, ownership,
    editorship, whatever.
    """
    user    = models.ForeignKey(User)
    code    = models.ForeignKey(Code)
    role    = models.CharField(max_length=100)
    
    # the following will be used in case of email relationship to keep track of last email (text of run object) that has been sent out
    # however it has been decided simply to drop the ScraperRunEvents onto a queue to be emailed, so we don't need this placeholder
    #lastrunobject = models.ForeignKey(ScraperRunEvent, null=True)

    def __unicode__(self):
        return "Scraper_id: %s -> User: %s (%s)" % (self.code, self.user, self.role)

    class Meta:
        app_label = 'codewiki'





# this is defunct.  should go
class UserCodeEditing(models.Model):
    """
    Updated by Twisted to state which scrapers/views are being editing at this moment
    """
    user    = models.ForeignKey(User, null=True)
    code = models.ForeignKey(Code, null=True)
    editingsince = models.DateTimeField(blank=True, null=True)
    runningsince = models.DateTimeField(blank=True, null=True)
    closedsince  = models.DateTimeField(blank=True, null=True)
    twisterclientnumber = models.IntegerField(unique=True)
    twisterscraperpriority = models.IntegerField(default=0)   # >0 another client has priority on this scraper

    def __unicode__(self):
        return "Editing: Scraper_id: %s -> User: %s (%d)" % (self.code, self.user, self.twisterclientnumber)

    class Meta:
        app_label = 'codewiki'
        

# This should be deleted
class CodeCommitEvent(models.Model):
    revision = models.IntegerField()

    def __unicode__(self):
        return unicode(self.revision)

    @models.permalink
    def get_absolute_url(self):
        return ('commit_event', [self.id])

    def content_type(self):
        return ContentType.objects.get(app_label="codewiki", model="CodeCommitEvent")

    class Meta:
        app_label = 'codewiki'
