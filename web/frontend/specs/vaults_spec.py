from nose.tools import assert_equals, raises
import urllib

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives

from frontend.models import UserProfile
from codewiki.models import Vault
from frontend.views import vault_users, invite_to_vault

import helper
from mock import Mock, patch

def setup():
    global profile
    global user
    username,password = 'test','pass'
    user = User.objects.create_user(username, '%s@example.com' % username, password)
    profile = user.get_profile()

@raises(PermissionDenied)
def ensure_freeloaders_cannot_create_vault():
    profile.change_plan('free')
    profile.create_vault(name='avault')

def ensure_paying_user_can_create_vault():
    for plan in ('individual', 'business', 'corporate'):
        yield user_plan_create_vault, plan

def ensure_vault_is_saved():
    profile.change_plan('individual')
    vault = profile.create_vault(name='avault')
    id = vault.id
    db_vault = Vault.objects.filter(id=id)[0]
    assert_equals(db_vault.user, user)

def user_plan_create_vault(plan):
    profile.change_plan(plan)
    vault = profile.create_vault(name='avault')
    assert_equals(vault.user, user)
    
@patch('frontend.views.invite_to_vault')
def ensure_vault_owner_can_invite_new_member_by_email(mock_invite):
    profile.change_plan('corporate')
    vault = profile.create_vault(name='invitevault')
    email = 'test@example.com'
    factory = helper.RequestFactory()
    url = '/vaults/%s/adduser/%s/' % (vault.id, urllib.quote(email))
    request = factory.get(url, 
      dict(HTTP_X_REQUESTED_WITH='XMLHttpRequest'))
    request.user = user
    response = vault_users(request, vault.id, email, 'adduser')
    assert mock_invite.called

@patch.object(EmailMultiAlternatives, 'send')
def ensure_invite_new_member_sends_email(mock_send):
    vault = profile.create_vault(name='invitevault')
    email = 'test@example.com'
    response = invite_to_vault(user, email, vault)
    assert mock_send.called

