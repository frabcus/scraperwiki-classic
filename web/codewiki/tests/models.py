from django.test import TestCase

from codewiki.models import Scraper
from django.contrib.auth.models import User

class Test__unicode__(TestCase):
    def test_scraper_name(self):
        self.assertEqual(
            'test_scraper',
            unicode(Scraper(title='Test Scraper', short_name='test_scraper'))
        )

class TestUserUserRole(TestCase):
    fixtures = ['test_data.json']

    def test_mouse(self):
        s = Scraper.objects.get(short_name='test_scraper')
        s = User.objects.get(username='test_user')
        s = User.objects.get(username='test_admin')

        self.assertEqual(len(s.useruserrole_set.all()), 0)



