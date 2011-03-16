import unittest, uuid
from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestRegistration(SeleniumTest):
    """
    Registration specific tests with the details of the successful 
    registration being required by further tests so that they can 
    log on.
    """
    login_fail = "Sorry, but we could not find that user, or the password was wrong"
    default_values = {
        "id_name" : "test user",
        "id_username": "test",
        "id_email": "test@scraperwiki.com",                
        "id_password1": "password",                
        "id_password2": "password",                               
    }
    

    def test_manage_profile(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        username = str( uuid.uuid4() ).replace('-', '_')
        email    = 'se_test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        password = str( uuid.uuid4() ).replace('-', '_')
        
        d = deepcopy( self.default_values )
        d["id_username"] = "se_test_%s" % (username,)        
        d["id_email"]   = email
        d["password1"]  = password
        d["password2"]  = password        
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present("signed in as"), msg='User is not signed in and should be')
        
        
        bio = 'A short description about this user'
        
        # Click on username to view the profile
        s.click('link=%s' % d['id_name'])
        self.wait_for_page()
        
        # Edit your profile
        s.click('link=Edit your profile')
        self.wait_for_page()
        
        # Change the name, bio and alert frequency before saving changes
        s.type('id_name','not just a test user')
        s.type('id_bio', bio)
        s.select('id_alert_frequency', 'label=never')
        s.click("//input[@value='Save changes']")
        self.wait_for_page()
        
        # Make sure that the bio we set is present
        self.failUnless(s.is_text_present("Registered email address"))        
        self.failUnless(s.is_text_present(bio), msg='Bio text is missing')                

    def test_create_valid(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        username = str( uuid.uuid4() ).replace('-', '_')
        email    = 'se_test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        password = str( uuid.uuid4() ).replace('-', '_')
        
        d = deepcopy( self.default_values )
        d["id_username"] = "se_test_%s" % (username,)        
        d["id_email"]   = email
        d["password1"]  = password
        d["password2"]  = password        
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present("signed in as"), msg='User should be logged in but is not')
        
        s.click('link=sign out')
        self.wait_for_page()
        
        SeleniumTest._valid_username = d["id_username"]        
        SeleniumTest._valid_password = password


    def test_invalid_email(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        d = deepcopy( self.default_values )
        d["email"] = "notanemail"
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present("Enter a valid e-mail address."), msg='Expected to fail for invalid email')

    def test_no_data(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()
        
        s.click('register')
        self.wait_for_page()
        
        self.failUnless(s.is_text_present("Please review the form and try again."), msg='Expected complaints about no data')


    def test_dupe_email(self):
        expected = 'This email address is already in use. Please supply a different email address. '
        s = self.selenium

        email = 'se_test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        for x in xrange(0,2):
            s.open("/")            
            s.click("link=Sign in or create an account")
            self.wait_for_page()
            
            username = str( uuid.uuid4() ).replace('-', '_')

            self.default_values["id_username"] = "se_test_%s" % (username,)        
            self.default_values["id_email"]   = email
            self.type_dictionary( self.default_values )
            
            s.click( 'id_tos' )
            s.click('register')
            self.wait_for_page()
            
            if x == 0:
                s.click("link=sign out")
                self.wait_for_page()
                
        self.failUnless(s.is_text_present(expected), 'Email was not already in use and was expected to be')


    def test_nonmatching_passwords(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()
        
        d = deepcopy( self.default_values )
        d["id_password1"] = "password1"
        d["id_password2"] = "password2"                               
        self.type_dictionary( d )
        
        s.click('register')
        self.wait_for_page()
        self.failUnless(s.is_text_present("The two password fields didn't match."), 
                        msg='Two password fields did not match and should have failed')


    def test_missing_terms(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()
        
        d = deepcopy( self.default_values )
        d["id_password1"] = "password1"
        d["id_password2"] = "password2"                               
        self.type_dictionary( d )

        s.click('register')
        self.wait_for_page()
        self.failUnless(s.is_text_present("You must agree to the ScraperWiki terms and conditions "), 
                        msg='Site is not complaining that user did not accept terms')

    def test_login_no_details(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        s.click('login')
        self.wait_for_page()
        self.failUnless(s.is_text_present(self.login_fail), msg='Login did not fail and it should have')        
        
        
    def test_login_only_username(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        s.type( 'id_user_or_email', 'abcdefghijklmnopqrstuvwxyz')
        s.click('login')
        self.wait_for_page()
        self.failUnless(s.is_text_present(self.login_fail), msg='Login did not fail even without password')                
        
    def test_login_junk_details(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        self.wait_for_page()

        s.type( 'id_user_or_email', 'abcdefghijklmnopqrstuvwxyz')
        s.type( 'id_password', 'abcdefghijklmnopqrstuvwxyz')
        
        
        s.click('login')
        self.wait_for_page()
        self.failUnless(s.is_text_present(self.login_fail), 'Login did not fail with fake details')                        
