import sys

import splinter
from lettuce import step,before,world,after

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
    print >> sys.stderr, open('mail.out').read()
    assert address in open('mail.out').read()
