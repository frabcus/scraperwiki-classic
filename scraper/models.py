from django.db import models
from django.contrib.auth.models import User

from page_cache.models import *

from django.core.mail import send_mail

# models defining scrapers and their metadata.

class ScraperManager(models.Manager):
    """
        This manager is implemented to allow you to link back to the particular scrapers through
        names defining their relationship to the user.

        So, having a user

        > user

        you can reference all scrapers that user has ownership of by

        > user.scraper_set.owns()

        and you can reference all the scrapers that user is watching by

        > user.scraper_set.watching()

        to check if this user owns any scrapers you can use

        > user.dont_own_any()

        or to check if the user is following any

        > user.not_watching_any()

    """
    use_for_related_fields = True
	
    def owns(self):
        return self.get_query_set().filter(userscraperrole__role='owner')
		
    def watching(self):
        return self.get_query_set().filter(userscraperrole__role='follow')

    # returns a list of the users own scrapers that are currently good.
    def owned_good(self):
        good_ones = []
        for scraper in self.owns():
            if scraper.is_good():
                good_ones.append(scraper)
                
        return good_ones;

    def owned_count(self):
        return len(self.owns())
        
    def owned_good_count(self):
        return len(self.owned_good())	
        
    def watching_count(self):
        return len(self.watching())
	
    def not_watching_any(self):
        return self.watching_count() == 0

    def dont_own_any(self):
        return self.owned_count() == 0
        
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
    title             = models.CharField(max_length = 100)
    short_name        = models.CharField(max_length = 50)
    source            = models.CharField(max_length = 100)
    last_run          = models.DateTimeField(blank = True, null=True)
    description       = models.TextField()
    license           = models.CharField(max_length = 100)
    created_at        = models.DateTimeField(auto_now_add = True)
    published_version = models.IntegerField()
    disabled          = models.BooleanField()
    deleted           = models.BooleanField()
    status            = models.CharField(max_length = 10)
    users             = models.ManyToManyField(User, through='UserScraperRole')

    objects = ScraperManager()

    def language(self):
	    return "Python"
	
    def record_count(self):
        return 12345

    def owner(self):
        return self.users.filter(userscraperrole__role='owner')[0]

    def followers(self):
        return self.users.filter(userscraperrole__role='follow')

    def is_published(self):
	    return self.status == 'Published'
	    
	# currently, the only editor we have is the owner of the scraper.
    def editors(self):
        return (self.owner(),)

    def current_code(self):
	    return """
# Scraper Code.
# Currently this is dummy data, as there is no storage of the code yet
	
print "Hello World"
               """

    def is_good(self):
        # don't know how goodness is going to be defined yet.
        return True
		

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

    def is_good(self):
        answer = True
        for invocation in self.scraperinvocation_set.all():
            if invocation.has_errors():
                answer = False
				
        return answer
			

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

    # XYZZY PRM 2009/09/30 - Hmmm, this definition means a scraper breaks when there is a transient error.
    # this needs to be discussed as obviously a transient network error should not be recorded as a broken
    # scraper.
    def has_errors(self):
        return len(self.scraperexception_set.all()) > 0

class ScraperException(models.Model):
    """
        If a scraper raises an exception while it is run, this fact is recorded here.
    """
    scraper_invocation = models.ForeignKey(ScraperInvocation)
    message            = models.CharField(max_length = 100)
    line_number        = models.IntegerField()
    backtrace          = models.TextField()

class UserScraperRole(models.Model):
    """
        This embodies the roles associated between particular users and scrapers. This should be used
        to store all user/scraper relationships, ownership, editorship, whatever.
    """
    user    = models.ForeignKey(User)
    scraper = models.ForeignKey(Scraper)
    role    = models.CharField(max_length = 100)

class PageAccess(models.Model):
    """
       When a scraper requests a page, we check to see whether it is already alive in the cache, if it is
       we don't actually go get it, we used the cached version.

       But, the record of whether a page is used by a scraper is recorded as an object of this class, linking
       the ScraperInvocation with the cached page.
    """
    cached_page        = models.ForeignKey(CachedPage)
    scraper_invocation = models.ForeignKey(ScraperInvocation)

class UserScraperRole(models.Model):
    """
        This embodies the roles associated between particular users and scrapers. This should be used
        to store all user/scraper relationships, ownership, editorship, whatever.
    """
    user    = models.ForeignKey(User)
    scraper = models.ForeignKey(Scraper)
    role    = models.CharField(max_length = 100)
    
class ScraperRequest(models.Model):
    """
       We wish to allow the users to put in their requests for what data to scrape next.
    """

    description = models.TextField()
    source_link = models.CharField(max_length = 250)
    created_at  = models.DateTimeField(auto_now_add = True)

    def send_notice_email(self):
        send_mail(self.email_subject(), self.email_body(), self.from_address(), self.recipient_list(), fail_silently=True)
        
    def email_subject(self):
        return "Scraper Request"
        
    def email_body(self):
        return """
    Dear Scraperwiki Developers,
    
       A scraper has been requested.
       
       The description is as follows :-
       
       %s
       
       From the source
       
       %s
        """ % (self.description, self.source_link)
        
    def from_address(self):
        return 'no-reply@scraperwiki.org'
        
    def recipient_list(self):
        return ('peter.morris@ntlworld.com',)