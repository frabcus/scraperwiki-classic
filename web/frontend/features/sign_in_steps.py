from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile
from nose.tools import assert_equals

prefix = 'http://localhost:8000'

@step("Given I am on the home page")
def given_i_am_on_the_home_page(step):
    world.browser.visit(prefix + '/')
    
@step("When I click the login link")
def when_i_click_the_login_link(step):
    world.browser.click_link_by_text("Log in")

@step("Then I should be on the login page")
def then_i_should_be_on_the_login_page(step):
    assert 'login' in world.browser.url

@step("Given I am on the login page")
def given_i_am_on_the_login_page(step):
    world.browser.visit(prefix + '/login')

@step('Given there is a username "([^"]*)" with password "([^"]*)"')
def make_user(step, username, password):
    us = list(User.objects.filter(username=username))
    if not us:
        # no users, no need to delete
        pass
    else:
        u = us[0]
        UserProfile.objects.filter(user=u).delete()
        u.delete()
    #create user
    user = User.objects.create_user(username, '%s@example.com' % username, password)
    user.save()

@step(r'When I fill in my username "([^"]*)" and my password "([^"]*)"')
def fill_in(step, username, password):
    world.browser.find_by_css('div#divContent [name=user_or_email]').first.fill(username)
    world.browser.find_by_css('div#divContent [name=password]').first.fill(password)

@step(r'''And I click the page's "([^"]*)" button''')
def click_button(step, button):
    world.browser.find_by_css('div#divContent').first.find_by_value(button).first.click()

@step('Then user "([^"]*)" is logged in')
def logged_in(step, username):
    assert world.browser.find_link_by_text(username)

