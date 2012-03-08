from lettuce import step,before,world,after
from lettuce.django import django_url

@step(u'When I enter "([^"]*)" in the search box')
def when_i_fill_in_the_search_box_with_text(step, text):
    element = world.browser.find_by_css('#nav_search_q')
    element.fill(text)
    element.type('\n')
