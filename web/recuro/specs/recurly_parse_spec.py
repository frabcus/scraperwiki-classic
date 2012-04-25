from nose.tools import assert_equals

from recuro.recurly_parser import Contact

def it_should_translate_new_account_in_to_xero_contact():
    xml = """
    <?xml version="1.0" encoding="UTF-8"?> <new_account_notification> <account> <account_code>3-test-20120424T152301</account_code> <username nil="true"></username> <email>test@testerson.com</email> <first_name>Test</first_name> <last_name>Testerson</last_name> <company_name></company_name> </account> </new_account_notification>
    """

    xero_contact = Contact(xml)
    assert_equals(xero_contact.number, "3-test-20120424T152301")
    assert_equals(xero_contact.name, None)
    assert_equals(xero_contact.first_name, "Test")
    assert_equals(xero_contact.last_name, "Testerson")
    assert_equals(xero_contact.email, "test@testerson.com")
