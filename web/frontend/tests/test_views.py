"""
At the moment, this only tests some frontend.views
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

import frontend

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

    def test_help(self):
        response = self.client.get(reverse('help'))
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

    def test_help_code_documentation(self):
        response = self.client.get(reverse('help_code_documentation'))
        self.assertEqual(response.status_code, 200)

    def test_help_tutorials(self):
        response = self.client.get(reverse('help_tutorials'))
        self.assertEqual(response.status_code, 200)

    def test_contact_form(self):
        response = self.client.get(reverse('contact_form'))
        self.assertEqual(response.status_code, 200)


