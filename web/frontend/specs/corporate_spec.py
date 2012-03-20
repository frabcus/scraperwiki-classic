import unittest

import django.core.mail
import mock
from frontend.views import corporate_contact

import helper

sent_mail_content = {}
def mock_sendmail(subject,message,from_email,recipient_list, **kwargs):
    global sent_mail_content
    sent_mail_content = dict(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list)

old_sendmail = django.core.mail.send_mail
django.core.mail.send_mail = mock_sendmail

def ensure_email_is_sent_on_corporate_contact_post():
    rf = helper.RequestFactory()
    data = {'callback_name'     : 'Test Testerson',
            'callback_company'  : 'Test Inc.',
            'callback_number'   : '800-282820' }

    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)

    assert sent_mail_content

def ensure_email_contains_contact_details():
    rf = helper.RequestFactory()
    data = {'callback_name'     : 'Test Testerson',
            'callback_company'  : 'Test Inc.',
            'callback_number'   : '800-282820' }

    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)

    # Check each form value (name, phone number, etc)
    # appears somewhere in the message.
    for item in data.values():
        assert item in sent_mail_content['message']

