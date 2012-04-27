import string

from lxml import etree,html

from recuro.xero import XeroPrivateClient

def parse(body):
    if '<new_account_notification>' in body:
        return Contact(body)
    if '<successful_payment_notification>' in body:
        return Invoice(body)

class Contact(XeroPrivateClient):
    def __init__(self, xml=None, **k):
        # Example XML in specs/recurly_parse_spec.py
        doc = html.fromstring(xml.encode('UTF-8'))
        self.number = doc.xpath('//account_code')[0].text
        self.name = doc.xpath('//company_name')[0].text
        self.first_name = doc.xpath('//first_name')[0].text
        self.last_name = doc.xpath('//last_name')[0].text
        self.email = doc.xpath('//email')[0].text

        if self.name is None:
            self.name = "%s %s" % (self.first_name, self.last_name)
        super(Contact, self).__init__(**k)


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
    def __init__(self, xml=None, **k):
        # Example XML in specs/recurly_parse_spec.py
        doc = html.fromstring(xml.encode('UTF-8'))
        # Map recurly account code to xero contact number.
        self.contact_number = doc.xpath('//account_code')[0].text
        self.amount_in_cents = int(
          doc.xpath("//amount_in_cents")[0].text)
        self.invoice_date = doc.xpath('//date')[0].text
        self.status = 'UNKNOWN'
        if 'successful_payment_notification' in xml:
            self.status = 'PAID'
        self.invoice_number = ('RECURLY' +
          doc.xpath('//invoice_number')[0].text)

        super(Invoice, self).__init__(**k)

    def to_xml(self):
        template = string.Template("""
          <Invoice>
            <InvoiceNumber>$invoice_number</InvoiceNumber>
            <Type>ACCREC</Type>
            <Contact>
              <ContactNumber>$contact_number</ContactNumber>
            </Contact>
            <Date>$short_date</Date>
            <DueDate>$short_date</DueDate>
            <CurrencyCode>USD</CurrencyCode>
            <LineItems>
              <LineItem>
                <Description>ScraperWiki Vault</Description>
                <Quantity>1</Quantity>
                <UnitAmount>$price</UnitAmount>
                <AccountCode>200</AccountCode>
              </LineItem>
            </LineItems>
          </Invoice>
          """)
        price = "%.2f" % (self.amount_in_cents/100.0)
        short_date = self.invoice_date[:10]
        return template.substitute(price=price, short_date=short_date,
          **self.__dict__)
