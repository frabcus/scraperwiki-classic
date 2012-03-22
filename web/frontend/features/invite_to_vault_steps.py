import splinter
from lettuce import step,before,world,after

@step(u'(?:Then|And) I type in "([^"]*)" in the email box$')
def then_i_type_in_the_email_box(step, text):
    world.browser.find_by_css('#username').first.fill(text)
