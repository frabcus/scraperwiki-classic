import unittest, uuid, time
from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestScrapers(SeleniumTest):
    
    def test_create(self):
        name = str( uuid.uuid4() )
        print 'Scraper will be called ', name
        
        s = self.selenium
        s.open("/logout")
        self.login( 'wewe', 'pass' )
        
        s.answer_on_next_prompt( name )        
        s.click('link=New scraper')        
        time.sleep(1)        
        s.click( 'link=Blank Python scraper' )
        s.wait_for_page_to_load("30000")      
        s.type('//body[@class="editbox"]', "print 'hello'")        
        s.click('btnCommitPopup')
        s.wait_for_page_to_load("30000")      
        time.sleep(1)



        
