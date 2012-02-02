from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals
from splinter.browser import Browser
from selenium.webdriver.support.ui import WebDriverWait

prefix = 'http://localhost:8000'

@before.all
def set_browser():
    world.browser = Browser()

@step(u'When I visit the pricing page')
def when_i_visit_the_pricing_page(step):
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

    clear_obscuring_popups(world.browser)

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

@step(u'(?:And|Then) I should see "([^"]*)"')
def and_i_should_see(step, text):
    assert world.browser.is_text_present(text)

@step(u'Given I have chosen the "([^"]*)" plan')
def given_i_have_chosen_a_plan(step, plan):
    step.behave_as('Given user "test" with password "pass" is logged in')
    world.browser.visit(prefix + '/subscribe/%s' % plan.lower())
    wait_for_element_by_css('.card_number')

@step(u'When I enter my contact information')
def when_i_enter_my_contact_information(step):
    contact_info = world.browser.find_by_css('.contact_info').first
    contact_info.find_by_css('.first_name input').first.fill('Test') 
    contact_info.find_by_css('.last_name input').first.fill('Testerson') 
    contact_info.find_by_css('.email input').first.fill('test@testerson.com') 

@step(u'And I enter "([^"]*)" as the billing name')
def and_i_enter_the_billing_name(step, billing_name):
    billing_info = world.browser.find_by_css('.billing_info').first
    billing_info.find_by_css('.first_name input').first.fill('Test') 
    billing_info.find_by_css('.last_name input').first.fill('Testerson') 

@step(u'And I enter "([^"]*)" as the credit card number')
def and_i_enter_the_credit_card_number(step, number):
    billing_info = world.browser.find_by_css('.billing_info').first
    billing_info.find_by_css('.card_number input').first.fill(number) 

@step(u'And I enter "([^"]*)" as the CVV')
def and_i_enter_the_cvv(step, cvv):
    billing_info = world.browser.find_by_css('.billing_info').first
    billing_info.find_by_css('.cvv input').first.fill(cvv) 
    
@step(u'And I enter "([^"]*)" as the expiry month and year')
def and_i_enter_the_expiry_month_and_year(step, expiry):
    month, year = expiry.split('/')
    # The option value for month does not have a leading 0.
    month = str(int(month))
    world.browser.find_option_by_value(month).first.check()
    # Convert 2-digit year to 21st Century!
    year = "20%s" % year
    world.browser.find_option_by_text(year).first.check()

@step(u'And I enter the billing address')
def and_i_enter_the_billing_address(step):
    div = world.browser.find_by_css('.billing_info').first
    div.find_by_css('.address1 input').first.fill('ScraperWiki Limited')
    div.find_by_css('.address2 input').first.fill('146 Brownlow Hill')
    div.find_by_css('.city input').first.fill('Liverpool')
    div.find_by_css('.zip input').first.fill('L3 5RF')
    world.browser.find_option_by_value('GB').first.check()
    div.find_by_css('.state input').first.fill('MERSEYSIDE')

@step(u'And I click "([^"]*)"')
def and_i_click(step, text):
    # :todo: Make it not wrong.  so wrong.
    world.browser.find_by_tag("button").first.click()

# :todo: Useful function, but probably should be kept somewhere else.
def wait_for_fx(timeout=5):
    WebDriverWait(world.browser.driver, timeout).until(lambda _d:
      world.browser.evaluate_script('jQuery.queue("fx").length == 0'))

# :todo: Useful function, but probably should be kept somewhere else.
def wait_for_element_by_css(css, timeout=5):
    WebDriverWait(world.browser.driver, timeout).until(lambda _d:
      len(world.browser.find_by_css(css)) != 0)

# :todo: Useful function, but probably should be kept somewhere else.
def clear_obscuring_popups(browser):
    """Clear alerts and windows that would otherwise obscure buttons.
    """

    for id in ["djHideToolBarButton", "alert_close"]:
        elements = browser.find_by_id(id)
        if not elements:
            continue
        element = elements.first
        if element.visible:
            element.click()
