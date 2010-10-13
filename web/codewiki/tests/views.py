"""
At the moment, this only tests some scraper.views
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

import scraper

class ScraperViewsTests(TestCase):
    fixtures = ['./fixtures/test_data.json']
    
    def test_scraper_list(self):
        """
        test
        """
        response = self.client.get(reverse('scraper_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_scraper_overview(self):
        response = self.client.get(reverse('code_overview', 
                            kwargs={'wiki_type':'scraper', 'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)
    
    def test_scraper_map(self):
        response = self.client.get(reverse('scraper_map', 
                            kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)
    
    def test_scraper_history(self):
        response = self.client.get(reverse('scraper_history',
                            kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)
        
    def test_scraper_stringnot(self):
        self.assertEqual(scraper.views.stringnot('test'), 'test')
    
    def test_scraper_comments(self):
        response = self.client.get(reverse('scraper_comments',
                            kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)
    
    def test_scraper_download(self):
        response = self.client.get(reverse('scraper_download',
                            kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)

    def test_scraper_export_csv(self):
        response = self.client.get(reverse('export_csv',
                            kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)

    def test_scraper_all_tags(self):
        response = self.client.get(reverse('all_tags'))
        self.assertEqual(response.status_code, 200)

    def test_scraper_search(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('search', kwargs={'q': 'test'}))
        self.assertEqual(response.status_code, 200)

    def test_scraper_follow(self):
        self.client.login(username='test_user', password='123456')
        response = self.client.get(reverse('scraper_follow',
                kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 302)

    def test_scraper_unfollow(self):
        self.client.login(username='test_user', password='123456')
        response = self.client.get(reverse('scraper_unfollow',
                kwargs={'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 302)

