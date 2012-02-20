from django.contrib.auth.models import User
from lettuce import step,before,world,after
from nose.tools import assert_equals

from frontend.models import Feature

import re

prefix = 'http://localhost:8000'

@before.each_scenario
def set_scraper_name(waht):
    import random
    import string
    world.name = ''.join(random.choice(string.letters) for _ in range(6))
    world.name = 'schedule_test_' + world.name

@step(u'Given I am an? "([^"]*)" user')
def given_i_am_a_plan_user(step, plan):
    plan = plan.replace(' ', '').lower()
    step.behave_as("""
    Given user "test" with password "pass" is logged in
    And I have the "Self Service Vaults" feature enabled
    And I am on the "%s" plan
    """ % plan)

@step(u'(?:When|And) I visit its overview page')
def i_visit_its_overview_page(step):
    # Assume we're already on the overview page
    assert '/scrapers/' + world.name + '/' in world.browser.url

@step(u'(?:Then|And) I should see the privacy panel')
def i_should_see_the_privacy_panel(step):
    assert world.browser.find_by_css("#privacy_status")

@step(u'(?:Then|And) I should see the button to change the privacy settings')
def i_should_see_the_button_to_change_the_privacy_settings(step):
    assert world.browser.find_by_css("#show_privacy_choices")

@step(u'(?:When|And) I click the privacy button')
def i_click_the_privacy_button(step):
    world.browser.find_by_css("#collaboration .buttons li a").first.click()

@step(u'(?:When|And) I click the change privacy button')
def i_click_the_change_privacy_button(step):
    world.browser.find_by_css("#show_privacy_choices").first.click()

@step(u"(?:When|And) I visit my scraper's overview page$")
def and_i_am_on_the_scraper_overview_page(step):
    world.browser.visit(prefix + '/scrapers/test_scraper')

@step(u'(?:Then|And) I am on the scraper overview page$')
def and_i_am_on_the_scraper_overview_page(step):
    assert re.search('/scrapers/' + world.name + '/$', world.browser.url, re.I)

@step(u'(?:Given|And) I am on the "([^"]*)" plan')
def i_am_on_the_plan(step, plan):
    user = User.objects.get(username='test')
    profile = user.get_profile()
    profile.change_plan(plan)