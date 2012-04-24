from recuro import xero
from django.conf import settings

def it_can_import_xero():
    from recuro import xero

def it_can_authorise_with_xero():
    session = xero.authorise(settings.XERO_CONSUMER_KEY,
                             settings.XERO_CONSUMER_SECRET,
                             settings.XERO_RSA_KEY)
    assert session.request

def it_can_call_a_xero_function():
    session = xero.authorise(settings.XERO_CONSUMER_KEY,
                             settings.XERO_CONSUMER_SECRET,
                             settings.XERO_RSA_KEY)
    resp, content = session.request("/Contacts", "GET")
    print repr(content)
    assert resp['status'] == '200'

