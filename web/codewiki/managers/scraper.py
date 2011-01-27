import django.db
from django.db import models
from django.db import connection, backend, models
from django.db.models import Q
import settings
from collections import defaultdict
import re
import datetime
import types
from code import CodeManager
from datastore import  DataStore



class ScraperManager(CodeManager):
    #use_for_related_fields = True

    def get_query_set(self):
        return super(ScraperManager, self).get_query_set().filter(deleted=False)
            
    def owns(self):
        return self.get_query_set().filter(usercoderole__role='owner')
        
    def watching(self):
        return self.get_query_set().filter(usercoderole__role='follow')

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


    #for example lists
    def example_scrapers(self, user, count):
        scrapers = []
        if user.is_authenticated():
            scrapers = user.code_set.filter(usercoderole__role='owner', wiki_type='scraper', deleted=False, published=True)[:count]
        else:
            scrapers = self.filter(deleted=False, featured=True).order_by('first_published_at')[:count]
        
        return scrapers

    def get_emailer_for_user(self, user):
        try:
            queryset = self.get_query_set()
            queryset = queryset.filter(Q(usercoderole__role='owner') & Q(usercoderole__user=user))
            queryset = queryset.filter(Q(usercoderole__role='email') & Q(usercoderole__user=user))
            return queryset.latest('id')
        except:
            return None

    def create_emailer_for_user(self, user, last_run=None):
        if not last_run:
            last_run = datetime.datetime.now()

        scraper = self.create(title="%s's Email Alert Scraper" % (user.get_profile().name or user.username),
                              short_name="%s.emailer" % user.username,
                              published=True,
                              last_run=last_run)
        scraper.commit_code("""
import scraperwiki
emaillibrary = scraperwiki.utils.swimport("general-emails-on-scrapers")
print emaillibrary.EmailMessage()
                            """,
                            'Initial Commit',
                            user)
        scraper.add_user_role(user, 'owner')
        scraper.add_user_role(user, 'email')
