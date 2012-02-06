from nose.tools import assert_equals, raises

from frontend.models import UserProfile
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

def setup():
    global user
    username,password = 'test','pass'
    user = User.objects.create_user(username, '%s@example.com' % username, password)

@raises(PermissionDenied)
def ensure_freeloaders_cannot_create_vault():
    profile = user.get_profile()
    profile.change_plan('free')
    profile.create_vault(name='avault')
