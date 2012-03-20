from lettuce import step,before,world,after
from lettuce.django import django_url
from django.contrib.auth.models import User

import os

@step(u'(?:Then|And) I should see how ScraperWiki helps me with "([^"]*)"')
def i_should_see_how_scraperwiki_helps_me_with(step, subject):
    assert world.browser.find_by_css("#" + subject.lower())

@step(u'(?:Then|And) I should see a phone number')
def i_should_see_a_phone_number(step):
    assert world.browser.find_by_xpath("//a[starts-with(@href, 'tel:')]")

@step(u'(?:Then|And) I should see an email address')
def i_should_see_an_email_address(step):
    assert world.browser.find_by_xpath("//a[starts-with(@href, 'mailto:')]")

@step(u'(?:Then|And) I should see a call-back form')
def i_should_see_a_call_back_form(step):
    assert world.browser.find_by_css('form#callback')

@step(u'(?:Then|And) I should see a "([^"]*)" field')
def i_should_see_a_field(step, fieldname):
    assert world.browser.find_by_xpath("//input[contains(@name,%s)]" % fieldname)

@step(u'(?:Given|And) I am using an iPhone')
def i_am_using_an_iphone(step):
    # let's pretend to be an iPhone shall we?
    assert True

@step(u'(?:Then|And) I should see a mobile optimized site')
def i_should_see_a_mobile_optimized_site(step):
    tags = ["//meta[@name='HandheldFriendly' and @content='True']",
            "//meta[@name='MobileOptimized']",
            "//meta[@name='viewport' and contains(@content, 'width=device-width')]"]
    for t in tags:
        if not world.browser.find_by_xpath(t):
            assert False
    assert True

@step(u'(?:Then|And) I should see all the corporate services')
def i_should_see_all_the_corporate_services(step):
    terms = ['dashboard', 'PDF extractor', 'SLA', 'vault', 'integration']
    for t in terms:
        if not world.browser.is_text_present(t):
            assert False
    assert True

@step(u'(?:Then|And) the phone number should automatically start a call')
def the_phone_number_should_automatically_start_a_call(step):
    step.behave_as("Then I should see a phone number")
    
@step(u'(?:Then|And) the "([^"]*)" field should bring up the numeric keypad')
def the_field_should_bring_up_the_numeric_keypad(step, fieldname):
    assert world.browser.find_by_xpath("//input[contains(@name,%s) and @type='tel']" % fieldname)

@step(u'When I fill in my corporate contact details')
def when_i_fill_in_my_corporate_contact_details(step):
    browser = world.browser
    browser.find_by_css('#callback_name').first.fill('Test Testerson')
    browser.find_by_css('#callback_company').first.fill('T Testerson Inc.')
    browser.find_by_css('#callback_number').first.fill('614-555-TEST')

@step(u'Then an e-mail should be sent')
def then_an_e_mail_should_be_sent(step):
    assert "Test Testerson" in open('mail.out').read()

