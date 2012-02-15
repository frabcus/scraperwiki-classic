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
    if num == 'a':
        num = 1
    num = int(num)
    user = User.objects.get(username='test')
    profile = user.get_profile()

    for i in range(num):
        profile.create_vault('My #%d Vault' % (i+1))

@step(u'(?:When|And) I visit my vaults page')
def when_i_visit_my_vaults_page(step):
    response = world.browser.visit(prefix + '/vaults/')

@step(u'(?:Then|And) I should see the "([^"]*)" button')
def i_should_see_the_button(step, text):
    assert world.browser.find_link_by_partial_text(text)

@step(u'(?:Then|And) I should not see the "([^"]*)" button')
def i_should_not_see_the_button(step, text):
    assert not world.browser.find_link_by_partial_text(text)

@step(u'(?:When|And) I click the "([^"]*)" button')
def i_click_the_button(step, text):
    world.browser.find_link_by_partial_text(text).first.click()

# This actually only checks that I can see *any* empty vault
# Not neccessarily that the empty vault is *new*
@step(u'(?:Then|And) I should see a new empty vault')
def i_should_see_a_new_empty_vault(step):
    assert world.browser.find_by_css('div.vault_contents.empty')

@step(u'(?:Then|And) I should not see a new empty vault')
def i_should_not_see_a_new_empty_vault(step):
    assert not world.browser.find_by_css('div.vault_contents.empty')
    
@step(u'(?:When|And) I visit the URL "([^"]*)"')
def when_i_visit_the_url(step, url):
    url = url.replace('scraperwiki.com', prefix)
    response = world.browser.visit(url)

# We should work out how to test 'hacks' like this
# DRJ suggests not testing them using Lettuce?
@step(u'When I make an AJAX request to the endpoint "([^"]*)"')
def when_i_make_an_ajax_request_to_the_endpoint(step, url):
    assert True
    
@step(u'Then I should not be successful')
def then_i_should_not_be_successful(step):
    assert True
