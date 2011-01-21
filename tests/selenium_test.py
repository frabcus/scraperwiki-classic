import unittest
from selenium import selenium


class SeleniumTest(unittest.TestCase):

    _valid_username = ''
    _valid_password = ''    

    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*firefox", "http://localhost:8000/")
        self.selenium.start()

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
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)