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
    assert False, 'This step must be implemented'
    
@step(u'When I visit the its overview page')
def when_i_visit_the_its_overview_page(step):
    assert False, 'This step must be implemented'
    
@step(u'Then I should see the scheduling panel')
def then_i_should_see_the_scheduling_panel(step):
    assert False, 'This step must be implemented'
    
@step(u'And I should see the "([^"]*)" button')
def and_i_should_see_the_group1_button(step, group1):
    assert False, 'This step must be implemented'
    
@step(u'And I am on the scraper overview page')
def and_i_am_on_the_scraper_overview_page(step):
    assert False, 'This step must be implemented'
    
@step(u'When I click the "([^"]*)" button in the scheduling panel')
def when_i_click_the_group1_button_in_the_scheduling_panel(step, group1):
    assert False, 'This step must be implemented'
    
@step(u'Then I should see the scheduling options')
def then_i_should_see_the_scheduling_options(step):
    assert False, 'This step must be implemented'