import os, sys, unittest, uuid, time

from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestScrapers(SeleniumTest):
    """
    Creates and runs some scrapers in various languages.  Unfortunately we 
    can't 
    """
    def load_scraper(self, type='python'):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_scraper.txt' % type)
        try:
            f = open(thefile)
            code = f.read()
            f.close()
        except:
            code = '# No test scraper'
    
        return code
        
    
    def test_python_create(self):
        s = self.selenium        
        self.create_type( 'Blank Python scraper', 'python')
        s.click('run')
        time.sleep(3)
        if not s.is_text_present('runfinished'):
            self.fail('Running the scraper seemed to fail')
                     
    def test_ruby_create(self):  
        s = self.selenium                      
        self.create_type( 'Blank Ruby scraper', 'ruby')
        s.click('run')
        time.sleep(3)
        if not s.is_text_present('runfinished'):
            self.fail('Running the scraper seemed to fail')
                
    def test_php_create(self):   
        s = self.selenium                     
        self.create_type( 'Blank PHP scraper', 'php')   
        s.click('run')
        time.sleep(3)
        if not s.is_text_present('runfinished'):
            self.fail('Running the scraper seemed to fail')
            
    def create_user(self):
        s = self.selenium
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        username = str( uuid.uuid4() ).replace('-', '_')
        email    = 'test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        password = str( uuid.uuid4() ).replace('-', '_')

        d = {
            "id_name" : "test user",
            "id_username": "test",
            "id_email": "test@scraperwiki.com",                
            "id_password1": "password",                
            "id_password2": "password",                               
        }
        d["id_username"] = "test_%s" % (username,)        
        d["id_email"]   = email
        d["password1"]  = password
        d["password2"]  = password        
        print 'Username is %s' % (d["id_username"],)
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        s.click('register')
        s.wait_for_page_to_load("30000")
        
        self.failUnless(s.is_text_present("signed in as"))
        
            
    def create_type(self, link_name, type):
        name = str( uuid.uuid4() )
        print '%s scraper will be called %s' % (type, name,)
        
        s = self.selenium
        s.open("/logout")
        
        # Unfortunately currently we are dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier.  
        #self.login( 'wewe', 'pass' )
        self.create_user()
        
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



        
