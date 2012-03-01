from lettuce import step,before,world,after
from lettuce.django import django_url

@step("And I am on my profile page")
def profile_page(step):
    step.behave_as("""
        And I am on the contact page
        And I click the "Your Profile" button
        """)

@step('Then I should be on my edit profile page')
def edit_profile_page(step):
    assert 'profile' in world.browser.url
    assert 'edit' in world.browser.url

