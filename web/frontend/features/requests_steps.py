from lettuce import step,before,world
from django.contrib.auth.models import User
from django.conf import settings
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals,assert_less

import time
import re

service_xpath = "//h3[a[contains(strong,'%s')]]"

@step(u'And I click on "([^"]*)"')
def and_i_click_on_group1(step, text):
    el = world.browser.find_by_xpath("//a[text()='%s']" % text).first
    el.click()

@step(u'And I click the "([^"]*)" services button')
def and_i_click_the_group1_services_button(step, service):
    el = world.browser.find_by_xpath((service_xpath % service)+'/a').first
    el.click()

@step(u'(?:Then|And) I should see the "([^"]*)" service')
def then_i_should_see_the_services(step, plan):
    plans = world.browser.find_by_xpath(service_xpath % plan)
    assert_equals(1, len(plans))

@step(u'(?:Then|And) I should see a link to "([^"]*)"')
def then_i_should_see_a_link(step, url):
    nodes = world.browser.find_by_xpath("//a[@href='%s']" % url)
    assert_less(0, len(nodes))

@step(u'(?:And|Then) I should see "([^"]*)"$')
def then_i_should_see(step, text):
    assert world.browser.is_text_present(text)

@step(u'(?:And|Then) I should see a form to request data')
def then_i_should_see_a_form_to_request_data(step):
    assert world.browser.find_by_css("form#request")

@step(u'(?:And|When) I say I want "([^"]*)"')
def when_i_say_i_want(step, description):
    world.browser.find_by_css('#request #id_description').first.fill(description)

@step(u'(?:And|When) I enter my name "([^"]*)"')
def and_i_enter_my_name(step, name):
    world.browser.find_by_css('#request #id_name').first.fill(name)

@step(u'(?:And|When) I enter my phone number "([^"]*)"')
def and_i_enter_my_phone_number(step, phone_number):
    world.browser.find_by_css('#request #id_phone').first.fill(phone_number)

@step(u'Then it should send an email to the feedback address')
def then_it_should_send_an_email_to_the_feedback_address(step):
    time.sleep(0.5)
    m = re.search(r"^To:\s+%s" % settings.FEEDBACK_EMAIL,
      open('mail.out').read(),
      re.M)
    assert m

@step(u'Then it should not send an email to the feedback address')
def then_it_should_not_send_an_email_to_the_feedback_address(step):
    assert False



