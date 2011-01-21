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
    login_fail = "Sorry, but we could not find that username or email address"
    default_values = {
        "id_name" : "test user",
        "id_username": "test",
        "id_email": "test@scraperwiki.com",                
        "id_password1": "password",                
        "id_password2": "password",                               
    }
    

    def test_create_valid(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        username = str( uuid.uuid4() ).replace('-', '_')
        email    = 'test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        password = str( uuid.uuid4() ).replace('-', '_')
        
        d = deepcopy( self.default_values )
        d["id_username"] = "test_%s" % (username,)        
        d["id_email"]   = email
        d["password1"]  = password
        d["password2"]  = password        
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        s.wait_for_page_to_load("30000")
        
        self.failUnless(s.is_text_present("signed in as"))
        
        s.click('link=sign out')
        s.wait_for_page_to_load("30000")      
        
        SeleniumTest._valid_username = d["id_username"]        
        SeleniumTest._valid_password = password


    def test_invalid_email(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        d = deepcopy( self.default_values )
        d["email"] = "notanemail"
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        s.wait_for_page_to_load("30000")
        
        self.failUnless(s.is_text_present("Enter a valid e-mail address."))

    def test_no_data(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")
        
        s.click('register')
        s.wait_for_page_to_load("30000")
        
        self.failUnless(s.is_text_present("Please review the form and try again."))


    def test_dupe_email(self):
        expected = 'This email address is already in use. Please supply a different email address. '
        s = self.selenium

        email = 'test_%s@scraperwiki.com' % str( uuid.uuid4() ).replace('-', '_')
        for x in xrange(0,2):
            s.open("/")            
            s.click("link=Sign in or create an account")
            s.wait_for_page_to_load("30000")
            
            username = str( uuid.uuid4() ).replace('-', '_')

            self.default_values["id_username"] = "test_%s" % (username,)        
            self.default_values["id_email"]   = email
            self.type_dictionary( self.default_values )
            
            s.click( 'id_tos' )
            s.click('register')
            s.wait_for_page_to_load("30000")    
            
            if x == 0:
                s.click("link=sign out")
                s.wait_for_page_to_load("30000")
                
        self.failUnless(s.is_text_present(expected))


    def test_nonmatching_passwords(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")
        
        d = deepcopy( self.default_values )
        d["id_password1"] = "password1"
        d["id_password2"] = "password2"                               
        self.type_dictionary( d )
        
        s.click('register')
        s.wait_for_page_to_load("30000")
        self.failUnless(s.is_text_present("The two password fields didn't match."))


    def test_missing_terms(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")
        
        d = deepcopy( self.default_values )
        d["id_password1"] = "password1"
        d["id_password2"] = "password2"                               
        self.type_dictionary( d )

        s.click('register')
        s.wait_for_page_to_load("30000")
        self.failUnless(s.is_text_present("You must agree to the ScraperWiki terms and conditions "))

    def test_login_no_details(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        s.click('login')
        s.wait_for_page_to_load("30000")                      
        self.failUnless(s.is_text_present(self.login_fail))        
        
    def test_login_only_username(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        s.type( 'id_user_or_email', 'abcdefghijklmnopqrstuvwxyz')
        s.click('login')
        s.wait_for_page_to_load("30000")                      
        self.failUnless(s.is_text_present(self.login_fail))                
        
    def test_login_junk_details(self):
        s = self.selenium
        s.open("/")
        s.click("link=Sign in or create an account")
        s.wait_for_page_to_load("30000")

        s.type( 'id_user_or_email', 'abcdefghijklmnopqrstuvwxyz')
        s.type( 'id_password', 'abcdefghijklmnopqrstuvwxyz')
        
        
        s.click('login')
        s.wait_for_page_to_load("30000")                      
        self.failUnless(s.is_text_present(self.login_fail))                        