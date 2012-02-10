from lettuce import step,before,world
from nose.tools import assert_equals
from splinter.browser import Browser
from selenium.webdriver.support.ui import WebDriverWait

prefix = 'http://localhost:8000'

@before.all
def set_browser():
    world.browser = Browser()

@step(u'Given that I have a scraper')
def given_that_i_have_a_scraper(step):
    import random
    import string

    step.behave_as("""
    Given user "test" with password "pass" is logged in
    And I click the button "Create a scraper"
    """)
    world.browser.find_link_by_href("/scrapers/new/python").first.click()
    world.browser.find_by_value("save scraper").first.click()
    # See http://splinter.cobrateam.info/docs/iframes-and-alerts.html
    prompt = world.browser.get_alert()
    name = ''.join(random.choice(string.letters) for _ in range(6))
    prompt.fill_with('schedule_test_' + name)
    prompt.accept()
    world.browser.find_by_id("back_to_overview").first.click()

@step(u'And I click the button "([^"]*)"')
def and_i_click(step, text):
    world.browser.find_link_by_partial_text(text).first.click()
    
@step(u'When I visit its overview page')
def when_i_visit_its_overview_page(step):
    # Assume we're already on the overview page
    assert '/scrapers/' in world.browser.url
    
@step(u'Then I should see the scheduling panel')
def then_i_should_see_the_scheduling_panel(step):
    assert world.browser.find_by_css(".schedule")
    
@step(u'And I should see the button to edit the schedule')
def and_i_should_see_the_button(step):
    assert world.browser.find_by_css("a.edit_schedule")
    
@step(u'And I am on the scraper overview page')
def and_i_am_on_the_scraper_overview_page(step):
    assert False, 'This step must be implemented'
    
@step(u'When I click the "([^"]*)" button in the scheduling panel')
def when_i_click_the_group1_button_in_the_scheduling_panel(step, group1):
    assert False, 'This step must be implemented'
    
@step(u'Then I should see the scheduling options')
def then_i_should_see_the_scheduling_options(step):
    assert False, 'This step must be implemented'
