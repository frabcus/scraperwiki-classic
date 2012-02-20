from lettuce import step,before,world
from django.contrib.auth.models import User

@step("When I click the login link")
def when_i_click_the_login_link(step):
    world.browser.click_link_by_text("Log in")

@step('Given there is a username "([^"]*)" with password "([^"]*)"')
def make_user(step, username, password):
    if username == 'test':
        # Should already have been created in the test-fixture
        # fixture file; so no need to create it here.
        return
    user = User.objects.create_user(username,
      '%s@example.com' % username, password)
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

