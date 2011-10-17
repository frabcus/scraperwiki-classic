from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

import frontend
from codewiki.models import Scraper, Code

class APIViewsTests(TestCase):
    fixtures = ['test_data']

    def test_scraper_search(self):
        scrapers = Code.objects.filter(title__icontains="test")
        response = self.client.get(reverse('api:method_search', kwargs={})) #'query':'test', 'format':'csv'}))
        self.assertEqual(response.status_code, 200)
        raise(response.content)
        self.assertEqual(response.context['scrapers_num_results'], 1)
    
#    def test_user_search(self):
#        scrapers = Code.objects.filter(title__icontains="Generalpurpose")
#        response = self.client.get(reverse('search', kwargs={'q':'test'}))
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(response.context['users_num_results'], 1)
    



