import unittest
import atexit
from selenium import selenium


# XXX make this a static member
def SeleniumTest_atexit():
    SeleniumTest._selenium.stop()

class SeleniumTest(unittest.TestCase):

    _valid_username = ''
    _valid_password = ''    

    _selenium_host = ''
    _selenium_port = 4444
    _selenium_browser = None

    _selenium = None

    _app_url = ''

    _verbosity = 1

    def setUp(self):
        self.verificationErrors = []

        # make singleton Selenium connection and new browser window
        if SeleniumTest._selenium == None:
            SeleniumTest._selenium = selenium(SeleniumTest._selenium_host, SeleniumTest._selenium_port, 
                                     SeleniumTest._selenium_browser, SeleniumTest._app_url)
            SeleniumTest._selenium.start()

            # make sure we quit the selenium when the script dies
            atexit.register(SeleniumTest_atexit)
        self.selenium = SeleniumTest._selenium
        self.selenium.delete_all_visible_cookies()
        #do_command('deleteAllCookies', [])
            
        # extract a title for the job from name of test.  must be done in the constructor or after start()
        self.selenium.set_context("sauce:job-name=%s" % self._testMethodName)  
        self.selenium.window_maximize()

    def wait_for_page(self, doing=None):
        hit_limit = True
        # DO NOT call anything else (even for debugging, e.g. self.selenium.get_location) at this point as:
        # "Running any other Selenium command after turns the flag to false."
        # http://release.seleniumhq.org/selenium-remote-control/0.9.2/doc/dotnet/Selenium.DefaultSelenium.WaitForPageToLoad.html
        try:
            self.selenium.wait_for_page_to_load('30000')
            hit_limit = False
        except:
            print 'Failed to load page in first 30 seconds, adding another 30'
        
        if hit_limit:
            try:
                self.selenium.wait_for_page_to_load('30000')
                hit_limit = False
            except:
                if not doing:
                    msg = 'It took longer than 60 seconds to visit %s, it may have failed' % self.selenium.get_location()
                else:
                    msg = 'It took longer than 60 seconds to: %s' % doing
                self.fail(msg=msg)

        if self._verbosity > 1:
            print "  waiting_for_page done, now at", self.selenium.get_location()


    def login(self, username, password):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        s.type( 'id_user_or_email', username)
        s.type( 'id_password', password)        
        
        s.click('login')
        s.wait_for_page_to_load("30000")                      
        
    def type_dictionary(self, d):
        for k,v in d.iteritems():
            self.selenium.type( k, v )
        
    def tearDown(self):
        self.assertEqual([], self.verificationErrors)


