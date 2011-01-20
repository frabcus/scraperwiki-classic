import os, sys, unittest, uuid, time

from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestScrapers(SeleniumTest):
    
    def load_scraper(self, type='python'):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_scraper.txt' % type)
        try:
            f = open(thefile)
            code = f.read()
            f.close()
        except:
            code = ''
    
        return code
        
    
    def test_python_create(self):
        self.create_type( 'Blank Python scraper', 'python')
        # TODO: Click on data tab and see what is there.
        
    def test_ruby_create(self):        
        self.create_type( 'Blank Ruby scraper', 'ruby')
        # TODO: Click on data tab and see what is there.
                
    def test_php_create(self):        
        self.create_type( 'Blank PHP scraper', 'php')                
        # TODO: Click on data tab and see what is there.    
    
    def create_type(self, link_name, type):
        name = str( uuid.uuid4() )
        print '%s scraper will be called %s' % (type, name,)
        
        s = self.selenium
        s.open("/logout")
        self.login( 'wewe', 'pass' )
        
        s.answer_on_next_prompt( name )        
        s.click('link=New scraper')        
        time.sleep(1)        
        s.click( 'link=%s' % link_name )
        s.wait_for_page_to_load("30000")      
        
        code = self.load_scraper(type)
        s.type('//body[@class="editbox"]', "%s" % code)        
        s.click('btnCommitPopup')
        s.wait_for_page_to_load("30000")      
        time.sleep(1)



        
