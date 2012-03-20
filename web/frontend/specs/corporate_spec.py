import unittest

import django.core.mail
import mock
from frontend.views import corporate_contact

import helper

send_mail_called = False

def ensure_email_is_sent_on_corporate_contact_post():
    def mock_sendmail(subject,message,from_email,recipients_list, **kwargs):
        global send_mail_called
        send_mail_called = True

    old_sendmail = django.core.mail.send_mail
    django.core.mail.send_mail = mock_sendmail
    rf = helper.RequestFactory()
    data = {'callback_name'     : 'Test Testerson',
            'callback_company'  : 'Test Inc.',
            'callback_number'   : '800-282820' }

    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)

    assert send_mail_called

    
