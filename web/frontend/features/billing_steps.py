from lettuce import step,before,world
from lettuce.django import django_url
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals
import time


@step(u'(?:Then|And) I should see the "([^"]*)" payment plan')
def then_i_should_see_the_payment_plan(step, plan):
    plan_name = world.browser.find_by_xpath(".//h3[text()='%s']" % plan)[0].text
    assert_equals(plan_name, plan)

@step(u'Given user "([^"]*)" with password "([^"]*)" is logged in')
def create_and_login(step, username, password):
    step.behave_as("""
    Given there is a username "%(username)s" with password "%(password)s"
    """ % locals())
    world.browser.visit(django_url('/contact/'))
    l = world.FakeLogin()
    cookie_data = l.login(username, password) 
    world.browser.driver.add_cookie(cookie_data)

@step(u'(?:Given|And) the "([^"]*)" feature exists')
def and_the_feature_exists(step, feature):
    Feature.objects.filter(name=feature).delete()
    Feature.objects.create(name=feature, public=True)

@step(u'(?:Given|And) I have the "([^"]*)" feature enabled')
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

@step(u'(?:And|Then) I should see "([^"]*)"$')
def and_i_should_see(step, text):
    assert world.browser.is_text_present(text)

@step(u'Given I have chosen the "([^"]*)" plan')
def given_i_have_chosen_a_plan(step, plan):
    username = 'test-%s' % time.strftime('%Y%m%dT%H%M%S')
    step.behave_as('Given user "%s" with password "pass" is logged in' % username)
    world.browser.visit(django_url('/subscribe/%s' % plan.lower()))
    world.wait_for_element_by_css('.card_number')

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

@step(u'(?:And|When) I click "([^"]*)"')
def and_i_click(step, text):
    # :todo: Make it not wrong.  so wrong.
    world.browser.find_by_tag("button").first.click()

@step(u'And I have entered my payment details')
def and_i_have_entered_my_payment_details(step):
    # Using Credit Card details for the recurly test gateway:
    # http://docs.recurly.com/payment-gateways/test-gateway
    step.behave_as("""
      When I enter my contact information
      And I enter "Test Testinator" as the billing name
      And I enter "02/13" as the expiry month and year
      And I enter "4111-1111-1111-1111" as the credit card number
      And I enter "666" as the CVV
      And I enter the billing address
      """)

@step(u'Then I should be on the vaults page')
def then_i_should_be_on_the_vaults_page(step):
    world.wait_for_url('/vaults')
    assert '/vaults' in world.browser.url

@step(u'And I already have the individual plan')
def and_i_already_have_the_individual_plan(step):
    from django.contrib.auth.models import User

    user = User.objects.get(username='test')
    profile = user.get_profile()
    profile.change_plan('individual')

@step(u'Then I should see "([^"]*)" in the individual box')
def then_i_should_see_text_in_the_individual_box(step, text):
    something = world.browser.find_by_xpath(
      ".//div[@id='%s']//*[text()='%s']" % ('individual', text))
    assert something

@step(u'(?:When|And) I enter the coupon code "([^"]*)"')
def i_enter_the_coupon_code(step, code):
    world.wait_for_element_by_css('.card_number')
    world.browser.find_by_css('input.coupon_code').first.fill(code)
    world.browser.find_by_css('div.coupon .check').first.click()
    world.wait_for_ajax()
