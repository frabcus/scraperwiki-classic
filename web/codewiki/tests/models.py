from django.test import TestCase

import codewiki

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

class TestUserUserRole(TestCase):
    def test_mouse(self):
        assert 1 == 2


