from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals
from selenium.webdriver.support.ui import WebDriverWait

prefix = 'http://localhost:8000'

@step(u'Given I am not logged in')
def given_i_am_not_logged_in(step):
    world.browser.cookies.delete()

@step(u'(?:When|And) I visit the pricing page')
def when_i_visit_the_pricing_page(step):
    response = world.browser.visit(prefix + '/pricing/')

@step(u'(?:Then|And) I should not see "([^"]*)"')
def and_i_should_not_see_text(step, text):
    assert world.browser.is_text_not_present(text)
