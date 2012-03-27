import sys
import re
import time

import splinter
from lettuce import step,before,world,after
from lettuce.django import django_url

@step(u'(?:When|And) I click the vault members button')
def i_click_the_vault_members_button(step):
    world.browser.find_by_css('div.vault').first.find_by_css('a.vault_users').first.click()
    world.wait_for_fx()

@step(u'(?:Then|And) I type "([^"]*)" into the username box$')
def i_type_into_the_username_box(step, text):
    world.browser.find_by_css('div.vault').first.find_by_css('input.username').first.fill(text)
    # Bit hacky, we may need to wait for the button to be truly visible.
    world.wait_for_element_by_css('.new_user a')

@step(u'Then an invitation email gets sent to "([^"]*)"')
def then_an_invitation_email_gets_sent_to(step, address):
    # Could check RE here, something like ("To:.*%s" % address).
    time.sleep(0.5) # need to wait a little bit for the mail, refactor!
    assert address in open('mail.out').read()

@step(u'Given I have been invited to scraperwiki')
def given_i_have_been_invited_to_scraperwiki(step):
    step.behave_as(
        """
        Given I am a "Corporate" user
        And I have a vault
        And I am on the vaults page
        When I click the vault members button
        And I click the "Add another user" button
        And I type "test@test.com" into the username box
        And I click the "Add!" button
        """)

@step(u'And there is a sign up link in the invitation email')
def and_there_is_a_sign_up_link_in_the_invitation_email(step):
    time.sleep(0.5)
    assert "/login/?t=" in open('mail.out').read()

@step(u'When I go to the invitation link in the email')
def when_i_go_to_the_invitation_link_in_the_email(step):
    # 3D is quoted printable nastiness
    token = re.search("/login/\?t=3D([a-fA-F0-9]{20})",
                open('mail.out').read()).group(1)
    world.browser.visit(django_url('/login/?t=%s' % token))

@step(u'When I fill in the registration form')
def when_i_fill_in_the_registration_form(step):
    world.browser.find_by_css('#id_name').first.fill('Lord Test Testington')
    world.browser.find_by_css('#id_email').first.fill('tt@lords.co.uk')
    world.browser.find_by_css('#id_password1').first.fill('pass')
    world.browser.find_by_css('#id_password2').first.fill('pass')
    world.browser.find_by_css('#id_tos').first.check()

@step(u'And I should have access to the vault I was invited to')
def and_i_should_have_a_vault(step):
    step.behave_as("""
                   When I visit the vaults page
                   Then I should see "My #1 Vault"
                   """)

