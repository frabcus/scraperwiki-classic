from django.test import TestCase
from django.core.urlresolvers import reverse as reverse_url
from datetime import datetime
import os.path
import unittest

from scraper import models

class Test__unicode__(TestCase):
    '''
    Simple test to verify the __unicode__ method
    of the various models doesn't work
    '''
    
    def test_scraper_long_name(self):
        self.assertEqual(
            'Test Scraper',
            unicode(models.Scraper(title='Test Scraper'))
        )
