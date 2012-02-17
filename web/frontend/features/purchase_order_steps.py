from lettuce import step,before,world
from django.contrib.auth.models import User
from frontend.models import UserProfile, Feature
from nose.tools import assert_equals

@step(u'Then I should see a message about paying with a purchase order')
def then_i_should_see_a_message_about_paying_with_a_purchase_order(step):
    assert world.browser.is_text_present('purchase order')

