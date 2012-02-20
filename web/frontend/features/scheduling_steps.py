from lettuce.django import django_url
from lettuce import step,before,world,after
from django.contrib.auth.models import User
from frontend.models import Feature
from codewiki.models import Scraper
import re
import time

@before.each_scenario
def reset_schedule(scenario):
    scraper = Scraper.objects.get(pk=1)    
    scraper.run_interval = -1
    scraper.save()
    
@step(u'Given I am an? "([^"]*)" user') 
def given_i_am_a_plan_user(step, plan):
    plan = plan.replace(' ', '').lower()
    step.behave_as("""
    Given user "test" with password "pass" is logged in
    And I have the "Self Service Vaults" feature enabled
    And I am on the "%s" plan
    """ % plan)

@step(u'And I click the button "([^"]*)"')
def and_i_click(step, text):
    world.browser.find_link_by_partial_text(text).first.click()
    
@step(u'Then I should see the scheduling panel')
def then_i_should_see_the_scheduling_panel(step):
    assert world.browser.find_by_css(".schedule")
    
@step(u'And I should see the button to edit the schedule')
def and_i_should_see_the_button(step):
    assert world.browser.find_by_css("a.edit_schedule")
    
@step(u"(?:When|And) I visit my scraper's overview page$")
def and_i_am_on_the_scraper_overview_page(step):
    world.browser.visit(django_url('/scrapers/test_scraper'))

@step(u'When I click the "([^"]*)" button in the scheduling panel')
def when_i_click_a_button_in_the_scheduling_panel(step, button):
    panel = world.browser.find_by_css("td.schedule").first
    panel.find_by_css("a." + button.lower()).first.click()
    world.wait_for_fx()
    
@step(u'Then I should see the following scheduling options:')
def then_i_should_see_the_scheduling_options(step):
    for label in step.hashes:
        xpath = ".//table[@id='edit_schedule']//label[text()=\"%s\"]" % label["Don't schedule"]
        assert world.browser.find_by_xpath(xpath)

@step(u'And I am on the "([^"]*)" plan')
def and_i_am_on_the_plan(step, plan):
    user = User.objects.get(username='test')
    profile = user.get_profile()
    profile.change_plan(plan)

@step(u'And I click the "([^"]*)" schedule option')
def when_i_click_the_schedule_option(step, option):
    xpath = ".//table[@id='edit_schedule']//label[text()=\"%s\"]" % option
    world.browser.find_by_xpath(xpath).first.click()
    world.wait_for_ajax()

@step(u'Then the scraper should be set to "([^"]*)"')
def then_the_scraper_should_be_set_to_schedule(step, schedule):
    step.behave_as('Then I should see "%s"' % schedule)

@step(u'And I should not see "([^"]*)"')
def and_i_should_not_see_text(step, text):
    assert world.browser.is_text_not_present(text)

@step(u'And I do not have the "([^"]*)" feature enabled$')
def feature_not_enabled(step, feature):
    u = User.objects.filter(username='test')[0]
    feature = Feature.objects.filter(name=feature)[0]
    profile = u.get_profile();

    try:
        profile.features.remove(feature)
    except ValueError:
        # Expected when the user already does not have the
        # feature in question.
        pass

    assert not profile.has_feature(feature)
