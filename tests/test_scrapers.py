import os, sys, unittest, uuid, time

from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestScrapers(SeleniumTest):
    """
    Creates and runs some scrapers in the three main supported languages. 
    
    Create
    Run
    Check
    "/scrapers/short_name/
    """
    def _load_data(self, type='python', obj='scraper'):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_%s.txt' % (type, obj,))
        try:
            f = open(thefile)
            code = f.read().replace('\n', '\r\n')
            f.close()
        except:
            code = '# No test object'
    
        return code
        
    
    def _check_dashboard_count(self, count=1):
        """ 
        Go to the current user's dashboard and make sure they 
        have a scraper there 
        """
        s = self.selenium
                
        s.click('link=Your dashboard')
        self.wait_for_page('visit dashboard')
        
        scraper_count = s.get_xpath_count('//li[@class="code_object_line"]')        
        self.failUnless( str(count) == scraper_count, msg='There are %s items instead of %s' % (scraper_count,count,) )
        

    def _check_clear_data(self, name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page')        
        s.click('btnClearDatastore')
        s.get_confirmation()
        self.wait_for_page('clear the datastore')
                    
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
            
        self.failUnless(s.is_text_present( 'This dataset has a total of 0 records' ), 
                        msg='The data does not appear to have been deleted')


    def _check_delete_scraper(self, name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % name)
        self.wait_for_page('view the scraper page')                
        s.click('btnDeleteScraper')
        s.get_confirmation()        
        self.wait_for_page('delete the scraper')
        
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
        
        self.failUnless(s.is_text_present( 'Your scraper has been deleted' ), msg='The scraper has not been deleted')


    def _check_delete_view(self, name):
        s = self.selenium     
                
        s.open('/views/%s/' % name)
        self.wait_for_page('view the scraper page')                
        s.click('btnDeleteScraper')
        s.get_confirmation()        
        self.wait_for_page()
        
        if s.is_text_present('Exception Location'):
            print s.get_body_text()
            self.fail('An error occurred deleting data')
        
        self.failUnless(s.is_text_present( 'Your view has been deleted' ), msg='The view has not been deleted')


    def _wait_for_run(self):
        """ We'll click run and then wait for 3 seconds, each time checking 
            whether we have in fact finished.  
        """
        self.selenium.click('run')
        success,total_checks = False, 12
        
        while not self.selenium.is_text_present('runfinished'):
            if total_checks == 0:
                self.fail('Running the scraper seemed to fail')
                return 
            time.sleep(3)
            total_checks -= 1
            
    
    def test_python_create(self):
        s = self.selenium        
        name = self._create_type( 'Blank Python scraper', 'python')
        self._wait_for_run()
        
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._check_dashboard_count()
        view_name = self._create_view('Blank Python view', 'python', name )
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )        
        self._check_dashboard_count(count=0)
                     
    def test_ruby_create(self):  
        s = self.selenium                      
        name = self._create_type( 'Blank Ruby scraper', 'ruby')
        self._wait_for_run()
                    
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._check_dashboard_count()                
        view_name = self._create_view('Blank Ruby view', 'ruby', name )        
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )
        self._check_dashboard_count(count=0)                             
        
                
    def test_php_create(self):   
        s = self.selenium                     
        name = self._create_type( 'Blank PHP scraper', 'php')   
        self._wait_for_run()
        
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._check_dashboard_count()
        view_name = self._create_view('Blank PHP view', 'php', name )                
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )                     
        self._check_dashboard_count(count=0)
                            
    def _create_user(self):
        s = self.selenium
        s.click("link=Sign in or create an account")
        self.wait_for_page()

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
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present("signed in as"), msg='User is not signed in and should be')
        
        
    def _create_type(self, link_name, type):
        name = str( uuid.uuid4() )
        
        s = self.selenium
        s.open("/logout")
        
        # Unfortunately we were dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier. So for now, we'll create a new 
        # user for each scraper/view pair
        self._create_user()
        
        s.answer_on_next_prompt( name )        
        s.click('link=New scraper')        
        time.sleep(1)        
        s.click( 'link=%s' % link_name )
        self.wait_for_page()
        
        code = self._load_data(type)
        s.type('//body[@class="editbox"]', "%s" % code)        
        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)
        return name
            
            
    def _create_view(self, link_name, type, shortname):
        """ Must be on the scraper homepage """
        s = self.selenium
        name = str( uuid.uuid4() )
        
        s.open('/scrapers/%s' % shortname)
        s.wait_for_page_to_load("30000")      
                
        s.answer_on_next_prompt( name )        
        s.click('link=Create a new view')        
        time.sleep(1)        
                
        s.click( 'link=%s' % link_name )
        self.wait_for_page()
        code = self._load_data(type,obj='view')
        code = code.replace('{{sourcescraper}}', name)
        
        s.type('//body[@class="editbox"]', "%s" % code)        
        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)
        
        
        return name


        
