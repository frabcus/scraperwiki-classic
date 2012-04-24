import lxml.html

class Contact():
    def __init__(self, xml):
        doc = lxml.html.fromstring(xml)
        self.number = doc.xpath('//account_code')[0].text
        self.name = doc.xpath('//company_name')[0].text
        self.first_name = doc.xpath('//first_name')[0].text
        self.last_name = doc.xpath('//last_name')[0].text
        self.email = doc.xpath('//email')[0].text
