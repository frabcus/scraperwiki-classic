import django.db
from django.db import models
from django.db.models import Q
from django.db import connection, backend, models
import settings
from collections import defaultdict
import re
import datetime
import types
from tagging.utils import get_tag
from tagging.models import Tag, TaggedItem

from datastore import  DataStore

class CodeManager(models.Manager):

    def scraper_search_query(self, user, query):
        if query:
            scrapers = self.get_query_set().filter(title__icontains=query)
            scrapers_description = self.get_query_set().filter(description__icontains=query)
            scrapers_all = scrapers | scrapers_description
        else:
            scrapers_all = self.get_query_set()
        scrapers_all = scrapers_all.exclude(privacy_status="deleted")
        if user and not user.is_anonymous():
            scrapers_all = scrapers_all.exclude(Q(privacy_status="private") & ~(Q(usercoderole__user=user) & Q(usercoderole__role='owner')) & ~(Q(usercoderole__user=user) & Q(usercoderole__role='editor')))
        else:
            scrapers_all = scrapers_all.exclude(privacy_status="private")
        scrapers_all = scrapers_all.order_by('-created_at')
        return scrapers_all.distinct()

