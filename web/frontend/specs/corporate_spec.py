import mock
from nose.tools import raises
from django.core.exceptions import ValidationError
from frontend.views import corporate_contact

import helper

rf = helper.RequestFactory()

def setup():
    global data
    data = {'callback_name'     : 'Test Testerson',
            'callback_company'  : 'Test Inc.',
            'callback_number'   : '800-282820' }

def ensure_email_is_sent_on_corporate_contact_post():
    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)
    assert helper.sent_mail_content

def ensure_email_contains_contact_details():
    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)
    # Check each form value (name, phone number, etc)
    # appears somewhere in the message.
    for item in data.values():
        assert item in helper.sent_mail_content['message']

def ensure_missing_name_errors():
    del data['callback_name']
    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)
    assert response.status_code == 400

def ensure_missing_company_errors():
    del data['callback_company']
    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)
    assert response.status_code == 400

def ensure_missing_number_errors():
    del data['callback_number']
    mock_request = rf.post('/corporate/contact/', data)
    response = corporate_contact(mock_request)
    assert response.status_code == 400
