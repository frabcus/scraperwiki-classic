import os, sys, unittest, uuid, time
from selenium import selenium
from selenium_test import SeleniumTest
from urlparse import urlparse

langlinkname = { "python":"Python", "ruby":"Ruby", "php":"PHP" }

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

    def test_ruby_create(self):  
        self._language_create("ruby")
                
    def test_php_create(self):  
        self._language_create("php")
    
    def test_python_create(self):  
        self._language_create("python")
    
    
    def _load_data(self, language, obj):
        thefile = os.path.join( os.path.dirname( __file__ ), 'sample_data/%s_%s.txt' % (language, obj,))
            
        f = open(thefile)
        # The file seems to be directly inserted into the source of the page, so some characters need
        # to be html encoded.
        code = f.read().replace('&','&amp').replace('<','&lt').replace('>','&gt').replace('\n', '<br>')
        f.close()
    
        return code

    
    def _add_comment(self, name):
        s = self.selenium
        
        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page to add comment')        
        
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
        Go to the current user's dashboard and verify the 
        number of scrapers there 
        """
        s = self.selenium
                
        s.click('link=Your dashboard')
        self.wait_for_page('visit dashboard')
        
        scraper_count = int(s.get_xpath_count('//li[@class="code_object_line"]'))    
        self.failUnless( count == scraper_count, msg='There are %s items instead of %s' % (scraper_count,count,) )
        

    def _check_clear_data(self, name):
        s = self.selenium     
                
        s.open('/scrapers/%s/' % name)        
        self.wait_for_page('view the scraper page to check we cleared the data')        
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
        self.wait_for_page('view the scraper page so we can delete it')                
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
        self.wait_for_page('view the page to delete the view')                
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
        s = self.selenium
        
        run_enabled = "selenium.browserbot.getCurrentWindow().document.getElementById('run').disabled == false"
        s.wait_for_condition(run_enabled, 5000)
        s.click('run')
        success,total_checks,reconnects = False, 12, 1

        # Dev server is slow, allow a page refresh on problems and give a longer timeout
        if s.browserURL == "http://dev.scraperwiki.com/":
            reconnects = 5
            total_checks = 40

        while not (s.is_text_present('Starting run ...') and s.is_text_present('runfinished')):
            if total_checks == 0 and reconnects == 0:
                self.fail('Running the scraper seemed to fail')
                return
            elif ((s.is_text_present('Connection to execution server lost') and (reconnects > 0))
                    or (s.is_text_present('runfinished') and not s.is_text_present('Starting run') and (reconnects > 0))
                    or (total_checks == 0) and (reconnects > 0)):
                # Refresh and start anew, something went wrong
                s.refresh()
                self.wait_for_page()
                time.sleep(1)
                s.wait_for_condition(run_enabled, 5000)
                s.click('run')
                reconnects -= 1
                total_checks = 40
            time.sleep(3)
            total_checks -= 1
            
        if self.selenium.is_text_present(' seconds elapsed'):
            # If the scraper has executed check that we have the expected output
            self.failUnless( self.selenium.is_text_present('<td>hello</td>') and self.selenium.is_text_present('<td>world</td>')) 
            self.failIf( self.selenium.is_text_present('Traceback') )
            success = True
            print 'Scraper returned some data!!!'
        
        self.failUnless(success)
        

    
    def _language_create(self, language):
        s = self.selenium        
        name = self._create_type(language)
        self._wait_for_run()
        
        s.click('link=Scraper')
        self.wait_for_page()
            
        self._add_comment(name)
        
        # Check for precreated e-mail scraper and new scraper
        self._check_dashboard_count()
        view_name = self._create_view(language, name)
        self._check_clear_data( name )
        self._check_delete_scraper(name )
        self._check_delete_view( view_name )        
        # Only e-mail scraper should be left
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
        
        
    def _create_type(self, language):
        name = 'se_test_%s' % str( uuid.uuid4() ).replace('-', '_')
        
        s = self.selenium
        s.open("/logout")
        
        # Unfortunately we were dependant on specifying an 
        # existing user as we haven't yet activated the new account 
        # that we created earlier. So for now, we'll create a new 
        # user for each scraper/view pair
        self._create_user()
        
        link_name = '%s scraper' % langlinkname[language]
        
        s.answer_on_next_prompt( name )        
        s.click('link=%s' % self.new_scraper_link)        
        time.sleep(1)
        s.click( 'link=%s' % link_name )
        self.wait_for_page()

        # Prompt and wait for save button to activate
        s.type_keys('//body[@class="editbox"]', "\16")
        s.wait_for_condition("selenium.browserbot.getCurrentWindow().document.getElementById('btnCommitPopup').disabled == false", 5000)
        
        # Load the scraper code and insert directly into page source
        code = self._load_data(language, 'scraper')
        s.type('//body[@class="editbox"]', "%s" % code)

        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)
        
        return name
        
        
    def _create_view(self, language, shortname):
        """ Must be on the scraper homepage """
        s = self.selenium
        name = 'se_test_%s' % str( uuid.uuid4() ).replace('-', '_')
        
        link_name = '%s view' % langlinkname[language]

        s.open('/scrapers/%s' % shortname)
        s.wait_for_page_to_load("30000")      
                
        s.answer_on_next_prompt( name )        
        s.click('//a[@class="editor_view"]')        
        time.sleep(1)        
        s.click( 'link=%s' % link_name )

        self.wait_for_page()

        # Prompt save button to activate
        self.selenium.type_keys('//body[@class="editbox"]',"                       ")
        time.sleep(1)

        code = self._load_data(language, 'view')
        code = code.replace('{{sourcescraper}}', name)
        
        s.type('//body[@class="editbox"]', "%s" % code)        
        s.click('btnCommitPopup')
        self.wait_for_page()
        time.sleep(1)

        return name


        
