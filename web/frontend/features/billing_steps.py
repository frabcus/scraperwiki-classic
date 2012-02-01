from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals
from splinter.browser import Browser

@before.all
def set_browser():
    world.browser = Browser()

@step(u'When I visit the pricing page')
def when_i_visit_the_pricing_page(step):
    prefix = 'http://localhost:8000'
    response = world.browser.visit(prefix + '/pricing/')

@step(u'(?:Then|And) I should see the "([^"]*)" payment plan')
def then_i_should_see_the_payment_plan(step, plan):
    plan_name = world.browser.find_by_xpath(".//h3[text()='%s']" % plan)[0].text
    assert_equals(plan_name, plan)

@step(u'Given user "([^"]*)" with password "([^"]*)" is logged in')
def create_and_login(step, username, password):
    step.behave_as("""
    Given there is a username "%(username)s" with password "%(password)s"
    Given I am on the login page
    When I fill in my username "%(username)s" and my password "%(password)s"
    And I click the button "Log in"
    """ % locals())

    assert world.browser.find_by_css('#nav_inner .loggedin')

    # Clear alerts and windows that would otherwise obscure buttons.
    for id in ["djHideToolBarButton", "alert_close"]:
        elements = world.browser.find_by_id(id)
        if not elements:
            continue
        element = elements.first
        if element.visible:
            element.click()

@step(u'And the "([^"]*)" feature exists')
def and_the_feature_exists(step, feature):
    Feature.objects.filter(name=feature).delete()
    Feature.objects.create(name=feature, public=True)

@step(u'And I have the "([^"]*)" feature enabled')
def and_i_have_a_feature_enabled(step, feature):
    u = User.objects.filter(username='test')[0]
    feature = Feature.objects.filter(name=feature)[0]
    profile = u.get_profile();
    profile.features.add(feature)
    assert profile.has_feature(feature)

@step(u'And I click on the "([^"]*)" "([^"]*)" button')
def and_i_click_on_a_plan_button(step, plan, button):
    el = world.browser.find_by_xpath(".//h3[text()='%s']/../p/a[text()='%s']" % (plan, button)).first
    el.click()

@step(u'Then I should be on the payment page')
def then_i_should_be_on_the_payment_page(step):
    assert '/subscribe' in world.browser.url

@step(u'And I should see "([^"]*)"')
def and_i_should_see(step, text):
    assert world.browser.is_text_present(text)

