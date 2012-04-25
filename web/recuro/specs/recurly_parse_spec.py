from nose.tools import assert_equals
from lxml import etree

from recuro.recurly_parser import Contact, parse

recurly_xml = """
    <?xml version="1.0" encoding="UTF-8"?> <new_account_notification> <account> <account_code>3-test-20120424T152301</account_code> <username nil="true"></username> <email>test@testerson.com</email> <first_name>Test</first_name> <last_name>Testerson</last_name> <company_name></company_name> </account> </new_account_notification>
      """
def it_detects_a_new_account_notification_and_creates_a_contact():
    obj = parse(recurly_xml)
    assert_equals(obj.__class__.__name__, "Contact")

def it_should_translate_new_account_in_to_contact_object():
    xero_contact = Contact(recurly_xml)
    assert_equals(xero_contact.number, "3-test-20120424T152301")
    assert_equals(xero_contact.first_name, "Test")
    assert_equals(xero_contact.last_name, "Testerson")
    assert_equals(xero_contact.email, "test@testerson.com")

def it_replaces_company_name_with_customer_name_if_not_present():
    xero_contact = Contact(recurly_xml)
    assert_equals(xero_contact.name, "Test Testerson")

def it_should_output_xero_contact_xml():
    xero_contact = Contact(recurly_xml)
    xero_xml = xero_contact.to_xml()
    doc = etree.fromstring(xero_xml)
    assert len(doc) > 0
    assert_equals(doc.xpath("//Contact/ContactNumber")[0].text,
                    "3-test-20120424T152301")
    assert_equals(doc.xpath("//Contact/Name")[0].text, "Test Testerson")
    assert_equals(doc.xpath("//Contact/FirstName")[0].text, "Test")
    assert_equals(doc.xpath("//Contact/LastName")[0].text, "Testerson")
    assert_equals(doc.xpath("//Contact/EmailAddress")[0].text,
                    "test@testerson.com")
