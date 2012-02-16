from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals,assert_less
import time

prefix = 'http://localhost:8000'

@step(u'When I visit the request page')
def when_i_visit_the_pricing_page(step):
    response = world.browser.visit(prefix + '/request_data/')

@step(u'(?:Then|And) I should see the "([^"]*)" services button')
def then_i_should_see_the_payment_plan(step, plan):
    plan_name = world.browser.find_by_xpath(".//h3/a/strong[text()='%s']" % plan)[0].text
    assert_equals(plan_name, plan)

@step(u'(?:Then|And) I should see a link to "([^"]*)"')
def then_i_should_see_the_payment_plan(step, url_expected):
    nodes = world.browser.find_by_xpath("//a[@href='%s']" % url)
    assert_less(0, len(nodes))

@step(u'(?:And|Then) I should see "([^"]*)"$')
def and_i_should_see(step, text):
    assert world.browser.is_text_present(text)
