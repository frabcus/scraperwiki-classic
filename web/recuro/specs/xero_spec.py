from recuro import xero
from recuro.xerokey import *

def it_can_import_xero():
    from recuro import xero

def it_can_authorise_with_xero():
    session = xero.authorise(XERO_CONSUMER_KEY, XERO_CONSUMER_SECRET, RSA_KEY)
    assert session.request

def it_can_call_a_xero_function():
    session = xero.authorise(XERO_CONSUMER_KEY, XERO_CONSUMER_SECRET, RSA_KEY)
    resp, content = session.request("/Contacts", "GET")
    print repr(content)
    assert resp['status'] == '200'

