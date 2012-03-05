from lettuce import step,before,world,after
from lettuce.django import django_url
from django.contrib.auth.models import User
import re

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
    r = False
    r = world.browser.find_by_xpath("//meta[@name='HandheldFriendly' and @content='True']")
    r = world.browser.find_by_xpath("//meta[@name='MobileOptimized']")
    r = world.browser.find_by_xpath("//meta[@name='viewport' and contains(@content, 'width=device-width')]")
    assert r

@step(u'(?:Then|And) the phone number should automatically start a call')
def the_phone_number_should_automatically_start_a_call(step):
    step.behave_as("Then I should see a phone number")
    
@step(u'(?:Then|And) the "([^"]*)" field should bring up the numeric keypad')
def the_field_should_bring_up_the_numeric_keypad(step, fieldname):
    assert world.browser.find_by_xpath("//input[contains(@name,%s) and @type='tel']" % fieldname)







