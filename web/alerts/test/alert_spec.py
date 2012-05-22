from nose.tools import assert_equals, raises
import sys
import urllib
import re
import datetime

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives

from codewiki.models import Vault, Scraper, ScraperRunEvent
from alerts.views import (
    alert_vault_members_of_exceptions,
    select_exceptions_that_have_not_been_notified,
    compose_email
    )

import helper
from mock import Mock, patch

def setUp():
    global profile
    global user
    global scraper
    global vault
    username,password = 'testing','pass'
    user = User.objects.create_user(username, '%s@example.com' % username, password)
    profile = user.get_profile()
    profile.plan = 'business'

def tearDown():
    vault.delete()
    scraper.delete()
    user.delete()

@patch.object(EmailMultiAlternatives, 'send')
def ensure_exceptionless_vault_receives_no_email(mock_send):
    vault = _make_vault_with_runevent('no_exceptions_vault', '')
    response = alert_vault_members_of_exceptions(vault)
    # make this work
    assert not mock_send.called

@patch.object(EmailMultiAlternatives, 'send')
def ensure_exceptional_vault_receives_email(mock_send):
    vault = _make_vault_with_runevent('yes_exceptions_vault', 'FakeError: This is a test.')
    response = alert_vault_members_of_exceptions(vault)
    assert mock_send.called

def _ensure_emails_contains_scraper_name(i):
    vault = _make_vault_with_runevent('yes_exceptions_vault', 'FakeError: This is a test.')
    runevents = select_exceptions_that_have_not_been_notified(user)
    assert "Bucket-Wheel Excavators" in compose_email(runevents, vault)[i]

def ensure_text_email_contains_scraper_name():
    _ensure_emails_contains_scraper_name('text')

def ensure_html_email_contains_scraper_name():
    _ensure_emails_contains_scraper_name('html')

def _make_vault_with_runevent(name, exception_message):
    global vault, scraper
    vault = profile.create_vault(name=name)
    scraper = Scraper.objects.create(
        title=u"Bucket-Wheel Excavators", vault = vault,
    )
    runevent = ScraperRunEvent.objects.create(
        scraper=scraper, pid=-1,
        exception_message=exception_message,
        run_started=datetime.datetime.now()
    )
    return vault
