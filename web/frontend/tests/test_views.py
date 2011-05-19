"""
At the moment, this only tests some frontend.views
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

import frontend
from codewiki.models import Scraper

class FrontEndViewsTests(TestCase):
    fixtures = ['./fixtures/test_data.json']
    
    def setUp(self):
        # make a dummy user...
        user = User(username='test', password='123')
        user.save()
        
    def test_profile_edit(self):
        self.client.login(username='test', password='123')
        response = self.client.post(reverse('profiles_edit_profile',), 
                                    {'bio' : 'updated bio',
                                    'alert_frequency' : 99})
        self.assertEqual(response.status_code, 302)

    def test_profile_view(self):
        user = User(username='test')
        response = self.client.get(reverse('profiles_profile_detail', 
                                            kwargs={'username' : user}))
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.post(reverse('login'), {'username': 'test',
                                                       'password': '123'})
        self.assertEqual(response.status_code, 200)

    def test_terms(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)

    def test_privacy(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_docs_ruby(self):
        response = self.client.get(reverse('docs', kwargs={'language': 'ruby'}))
        self.assertEqual(response.status_code, 200)

    def test_docs_python(self):
        response = self.client.get(reverse('docs', kwargs={'language': 'python'}))
        self.assertEqual(response.status_code, 200)

    def test_docs_php(self):
        response = self.client.get(reverse('docs', kwargs={'language': 'php'}))
        self.assertEqual(response.status_code, 200)

    def test_help(self):
        response = self.client.get('/help/', follow=True)
        self.assertEqual(response.redirect_chain, [('http://testserver/docs/', 301)])

    def test_contact_form(self):
        response = self.client.get(reverse('contact_form'))
        self.assertEqual(response.status_code, 200)

    def test_tutorials(self):    
        scraper = Scraper(title=u'Python1', language='python', istutorial=True)
        scraper.save()

        scraper = Scraper(title=u'Python2', language='python', istutorial=True)
        scraper.save()

        scraper = Scraper(title=u'Python3', language='python', istutorial=True)
        scraper.save()

        scraper = Scraper(title=u'PHP1', language='php', istutorial=True)
        scraper.save()

        scraper = Scraper(title=u'PHP2', language='php', istutorial=True)
        scraper.save()

        response = self.client.get(reverse('help', args=['tutorials', 'python']))
        self.assertEqual(response.status_code, 200)

        tutorials =  response.context['tutorials']
        self.assertTrue('python' in tutorials)
        self.assertEqual(3, len(tutorials['python']))

        response = self.client.get(reverse('help', args=['tutorials', 'php']))
        self.assertEqual(response.status_code, 200)

        tutorials =  response.context['tutorials']
        self.assertTrue('php' in tutorials)
        self.assertEqual(2, len(tutorials['php']))
