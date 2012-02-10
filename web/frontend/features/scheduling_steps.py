#from lettuce import step,before,world,after
from lettuce import *
from nose.tools import assert_equals
from splinter.browser import Browser
from selenium.webdriver.support.ui import WebDriverWait
import re
import sys

prefix = 'http://localhost:8000'

@before.all
def set_browser():
    import random
    import string
    if not world.browser: world.browser = Browser()
    world.name = ''.join(random.choice(string.letters) for _ in range(6))
    world.name = 'schedule_test_' + world.name

@after.all
def close_browser():
    world.browser.quit()

@step(u'Given that I have a scraper')
def given_that_i_have_a_scraper(step):
    step.behave_as("""
    Given user "test" with password "pass" is logged in
    And I click the button "Create a scraper"
    """)
    world.browser.find_link_by_href("/scrapers/new/python").first.click()
    world.browser.find_by_value("save scraper").first.click()
    # See http://splinter.cobrateam.info/docs/iframes-and-alerts.html
    prompt = world.browser.get_alert()
    prompt.fill_with(world.name)
    prompt.accept()
    world.browser.find_by_id("back_to_overview").first.click()

@step(u'And I click the button "([^"]*)"')
def and_i_click(step, text):
    world.browser.find_link_by_partial_text(text).first.click()
    
@step(u'When I visit its overview page')
def when_i_visit_its_overview_page(step):
    # Assume we're already on the overview page
    assert '/scrapers/' + world.name + '/' in world.browser.url
    
@step(u'Then I should see the scheduling panel')
def then_i_should_see_the_scheduling_panel(step):
    assert world.browser.find_by_css(".schedule")
    
@step(u'And I should see the button to edit the schedule')
def and_i_should_see_the_button(step):
    assert world.browser.find_by_css("a.edit_schedule")
    
@step(u'And I am on the scraper overview page')
def and_i_am_on_the_scraper_overview_page(step):
    assert re.search('/scrapers/' + world.name + '/$', world.browser.url, re.I)
    
@step(u'When I click the "([^"]*)" button in the scheduling panel')
def when_i_click_a_button_in_the_scheduling_panel(step, button):
    panel = world.browser.find_by_css("td.schedule").first
    panel.find_by_css("a." + button.lower()).first.click()
    
@step(u'Then I should see the following scheduling options:')
def then_i_should_see_the_scheduling_options(step):
    for label in step.hashes:
        xpath = ".//table[@id='edit_schedule']//label[text()=\"%s\"]" % label["Don't schedule"]
        assert world.browser.find_by_xpath(xpath)
