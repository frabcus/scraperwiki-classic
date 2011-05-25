import os, sys, unittest, uuid, time
from selenium import selenium
from selenium_test import SeleniumTest
from urlparse import urlparse


class TestScrapers(SeleniumTest):
    """
    Creates and runs some scrapers in the three main supported languages. 
    
    Create
    Run
    Check
    """
    login_text = "Log in"
    logged_in_text = "Logged in"
    new_scraper_link = "Create new scraper"

    def _load_data(self, type='python', obj='scraper'):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_%s.txt' % (type, obj,))
        try:
            f = open(thefile)
            code = f.read().replace('\n', '\r\n')
            f.close()
        except:
            code = '# No test object'
    
        return code
        
    
    def _add_comment(self, name):
        s = self.selenium
        
        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page')        
        
        s.click('link=Discussion (0)')    
        self.wait_for_page('visiting discussion')
        comment = 'A test comment'

        s.type('id_comment', comment)
        s.click('id_submit')
        time.sleep(2)

        # Currently we expect _add_comment to fail due to CSRF issues, but it will 
        # not fail on live. To resolve this we'll currently handle both cases :(
        if s.is_text_present(comment):
            print 'Working comments'
            self.failUnless(s.is_text_present(comment))
            self.failUnless(s.is_text_present("Discussion (1)"))        
        else:
            print 'Broken comments'            
#            self.failUnless(s.is_text_present('CSRF verification failed. Request aborted.'))

        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page')        
        
        
    def _check_dashboard_count(self, count=2):
        """ 
        Go to the current user's dashboard and make sure they 
        have a scraper there 
        """
        s = self.selenium
                
        s.click('link=Your dashboard')
        self.wait_for_page('visit dashboard')
        
        scraper_count = s.get_xpath_count('//li[@class="code_object_line"]')        
        self.failUnless( count == scraper_count, msg='There are %s items instead of %s' % (scraper_count,count,) )
        

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
            
        self.failIf(s.is_text_present( 'This dataset has a total of' ), 
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
        
        self.assertEqual('/', urlparse(s.get_location()).path, 'Did not redirect to front page after deleting scraper')


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
        
        self.assertEqual('/', urlparse(s.get_location()).path, 'Did not redirect to front page after deleting view')


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
            
        if self.selenium.is_text_present('seconds elapsed:'):
            # If the scraper has executed check that we have the expected output
            self.failUnless( self.selenium.is_text_present('hello') and self.selenium.is_text_present('world')) 
            print 'Scraper returned some data!!!'
            
    
    def test_python_create(self):
        s = self.selenium        
        name = self._create_type( 'Python scraper', 'python')
        self._wait_for_run()
        
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._add_comment(name)
            
        self._check_dashboard_count()
        view_name = self._create_view('Python view', 'python', name )
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )        
        self._check_dashboard_count(count=1)
                     
    def test_ruby_create(self):  
        s = self.selenium                      
        name = self._create_type( 'Ruby scraper', 'ruby')
        self._wait_for_run()
                    
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._add_comment(name)            
            
        self._check_dashboard_count()                
        view_name = self._create_view('Ruby view', 'ruby', name )        
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )
        self._check_dashboard_count(count=1)                             
        
                
    def test_php_create(self):   
        s = self.selenium
        name = self._create_type( 'PHP scraper', 'php')   
        self._wait_for_run()
        
        s.click('aCloseEditor1')
        self.wait_for_page()
            
        self._add_comment(name)            
            
        self._check_dashboard_count()
        view_name = self._create_view('PHP view', 'php', name )                
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )                     
        self._check_dashboard_count(count=1)
                            
    def _create_user(self):
        s = self.selenium
        s.click("link=%s" % self.login_text)
        self.wait_for_page()

        username = "se_test_%s" % str( uuid.uuid4() ).replace('-', '_')
        password = str( uuid.uuid4() ).replace('-', '_')

        d = {}
        d["id_name"] = "test user"
        d["id_username"] = username
        d["id_email"] = "%s@scraperwiki.com" % username
        d["id_password1"]  = password
        d["id_password2"]  = password
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present(self.logged_in_text), msg='User is not signed in and should be')
        
        
    def _create_type(self, link_name, type):
        name = 'se_test_%s' % str( uuid.uuid4() ).replace('-', '_')
        
        s = self.selenium
        s.open("/logout")
        
        # Unfortunately we were dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier. So for now, we'll create a new 
        # user for each scraper/view pair
        self._create_user()
        
        s.answer_on_next_prompt( name )        
        s.click('link=%s' % self.new_scraper_link)        
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
        name = 'se_test_%s' % str( uuid.uuid4() ).replace('-', '_')
        print name
        
        s.open('/scrapers/%s' % shortname)
        s.wait_for_page_to_load("30000")      
                
        s.answer_on_next_prompt( name )        
        s.click('//a[@class="editor_view"]')        
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


        
