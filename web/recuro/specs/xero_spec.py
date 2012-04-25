from recuro import xero
from django.conf import settings

session = None
def setup():
    global session
    session = xero.XeroPrivateClient(settings.XERO_CONSUMER_KEY,
                             settings.XERO_CONSUMER_SECRET,
                             settings.XERO_RSA_KEY)

def it_can_import_xero():
    from recuro import xero

def it_can_authorise_with_xero():
    assert session

def it_can_call_a_xero_function():
    # Is allowed access to internal _request method; it's
    # irrelevant which method gets called.  Don't think that this
    # allowance extends to you.
    resp, content = session._xero_request('/Contacts')
    print repr(content)
    assert resp['status'] == '200'

def it_can_add_a_contact():
    body="""<Contact>
      <Name>Test Testerson</Name>
    </Contact>
    """
    resp, content = session.contact_add(body)
    print repr(content)
    assert resp['status'] == '200'
