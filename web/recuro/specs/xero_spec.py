from recuro import xero

session = None
def setup():
    global session
    session = xero.XeroPrivateClient()

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

def it_can_post_an_xml_contact():
    class Contact(xero.XeroPrivateClient):
        def to_xml(self):
            return """<Contact>
              <Name>Test Testerson</Name>
            </Contact>
            """
    client = Contact()
    resp, content = client.save()
    print repr(content)
    assert resp['status'] == '200'
