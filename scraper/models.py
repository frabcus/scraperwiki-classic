from django.db import models
from django.contrib.auth.models import User

from page_cache.models import *

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
    disabled          = models.BooleanField()
    deleted           = models.BooleanField()
    status            = models.CharField(max_length = 10)

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
