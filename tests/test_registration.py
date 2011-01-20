import unittest, uuid
from copy import deepcopy
from selenium import selenium
from selenium_test import SeleniumTest


class TestRegistration(SeleniumTest):

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

        d = deepcopy( self.default_values )
        d["id_username"] = "test_%s" % (username,)                               
        print 'Username is %s' % (d["id_username"],)
        
        self.type_dictionary( d )
        s.click( 'id_tos' )
        
        s.click('register')
        s.wait_for_page_to_load("30000")
        
        self.failUnless(s.is_text_present("signed in as"))



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
