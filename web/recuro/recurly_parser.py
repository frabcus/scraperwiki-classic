import string

from lxml import etree,html

from recuro.xero import XeroPrivateClient

def parse(body):
    if '<new_account_notification>' in body:
        return Contact(body)
    if '<new_subscription_notification>' in body:
        return Invoice(body)

class Contact(XeroPrivateClient):
    def __init__(self, xml):
        doc = html.fromstring(xml.encode('UTF-8'))
        self.number = doc.xpath('//account_code')[0].text
        self.name = doc.xpath('//company_name')[0].text
        self.first_name = doc.xpath('//first_name')[0].text
        self.last_name = doc.xpath('//last_name')[0].text
        self.email = doc.xpath('//email')[0].text

        if self.name is None:
            self.name = "%s %s" % (self.first_name, self.last_name)

    def to_xml(self):
        template = string.Template( """
            <Contact>
                <ContactNumber>$number</ContactNumber>
                <Name>$name</Name>
                <FirstName>$first_name</FirstName>
                <LastName>$last_name</LastName>
                <EmailAddress>$email</EmailAddress>
            </Contact>
            """ )
        return template.substitute(number=self.number, name=self.name,
                        first_name=self.first_name, last_name=self.last_name,
                        email=self.email)

class Invoice(XeroPrivateClient):
    def __init__(self, xml):
        doc = html.fromstring(xml.encode('UTF-8'))
        self.contact = None # contact ID
        self.amount_in_cents = int(doc.xpath("//total_amount_in_cents")[0].text)

    def to_xml(self):
        return None
