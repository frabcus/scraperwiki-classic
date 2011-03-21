"""
At the moment, this only tests some scraper.views
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

import codewiki

class ScraperViewsTests(TestCase):
    fixtures = ['test_data.json']
    
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
    
    
    def _repo_exists( self, name ):
        """
        Check whether the repo exists, and create it if it does not. This is only used
        for testing and so should be safe.
        """
        from codewiki.vc import MercurialInterface
        from django.conf import settings
        from codewiki.models.scraper import Scraper
        
        m = MercurialInterface( settings.SMODULES_DIR )                    
        try:
            m.getfilestatus( 'test_scraper' )
        except:
            s = Scraper.objects.get(short_name=name)
            s.commit_code('#Test scraper for testing purposes only', 'test commit', s.owner())
            return False
        return True
    
    
    def test_scraper_history(self):
        if not self._repo_exists( 'test_scraper'):
            print "\n'test_scraper' doesn't exist - it is being created"
            
        response = self.client.get(reverse('scraper_history',
                            kwargs={'wiki_type':'scraper', 'short_name': 'test_scraper'}))
        self.assertEqual(response.status_code, 200)
        
    
    def test_scraper_comments(self):
        if not self._repo_exists( 'test_scraper'):
            print "\n'test_scraper' doesn't exist - it is being created"
            
        response = self.client.get(reverse('scraper_comments',
                            kwargs={'wiki_type':'scraper', 'short_name': 'test_scraper'}))
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

