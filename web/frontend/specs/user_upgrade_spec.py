from nose.tools import assert_equals

"""
from django.conf import settings
from django.http import HttpRequest
from django.test import Client
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.base import BaseHandler
"""

from frontend.models import UserProfile
from django.contrib.auth.models import User

def ensure_can_upgrade_account():
    username,password = 'test','pass'
    user = User.objects.create_user(username, '%s@example.com' % username, password)
    profile = user.get_profile()
    profile.change_plan('individual')
    assert_equals(profile.plan, 'individual')

