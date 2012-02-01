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
    assert plan_name == plan

@step(u"Given I'm logged in")
def given_i_m_logged_in(step):
    us = list(User.objects.filter(username='test'))
    if not us:
        # no users, no need to delete
        pass
    else:
        u = us[0]
        UserProfile.objects.filter(user=u).delete()
        u.delete()
    #create user
    user = User.objects.create_user('test', 'test@testerson.com', 'test')
    user.save()
    profile = UserProfile(user=user)
    success = world.browser.login(username='test', password='test') 

    response = world.browser.get('/')
    dom = html.fromstring(response.content)
    logged_in = dom.cssselect('#nav_inner .loggedin')
    assert logged_in != []

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
    world.href = world.dom.xpath(".//h3[text()='%s']/../p/a[text()='%s']" % (plan, button))[0].get('href')

@step(u'Then I should be on the payment page')
def then_i_should_be_on_the_payment_page(step):
    assert world.href.startswith('/subscribe')

@step(u'And I should see "([^"]*)"')
def and_i_should_see_group1(step, text):
    response = world.browser.get(world.href)
    assert text in response.content

