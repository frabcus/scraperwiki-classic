from lettuce import *
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals
from splinter.browser import Browser
from selenium.webdriver.support.ui import WebDriverWait

prefix = 'http://localhost:8000'

@before.all
def set_browser():
    if not world.browser: world.browser = Browser()

@after.all
def close_browser(total):
    if total.scenarios_ran == total.scenarios_passed:
        world.browser.quit()

@step(u'(?:Given|And) I am an? "([^"]*)" user') 
def given_i_am_a_plan_user(step, plan):
    plan = plan.replace(' ', '').lower()
    step.behave_as("""
    Given user "test" with password "pass" is logged in
    And I have the "Self Service Vaults" feature enabled
    And I am on the "%s" plan
    """ % plan)

@step(u'(?:Given|And) I have ([a0-9]) vaults?')
def and_i_have_a_vault(step, num):
    if num == 'a': num = 1
    num = int(num)
    user = User.objects.get(username='test')
    profile = user.get_profile()

    for i in range(1,num+1):
        profile.create_vault('My #%d Vault' % i)

@step(u'(?:When|And) I visit my vaults page')
def when_i_visit_the_pricing_page(step):
    response = world.browser.visit(prefix + '/vaults/')

@step(u'(?:Then|And) I should see the "([^"]*)" button')
def i_see_the_button(step, text):
    assert world.browser.find_link_by_partial_text(text)

@step(u'(?:Then|And) I should not see the "([^"]*)" button')
def i_see_the_button(step, text):
    assert not world.browser.find_link_by_partial_text(text)

@step(u'(?:When|And) I click the "([^"]*)" button')
def i_click_the_button(step, text):
    world.browser.find_link_by_partial_text(text).first.click()

# This actually only checks that I can see *any* empty vault
# Not neccessarily that the empty vault is *new*
@step(u'(?:Then|And) I should see a new empty vault')
def i_should_see_a_new_empty_vault(step):
    assert world.browser.find_by_css('div.vault_contents.empty')
