import unittest
from selenium import selenium


class SeleniumTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*firefox", "http://localhost:8000/")
        self.selenium.start()


    def type_dictionary(self, d):
        for k,v in d.iteritems():
            self.selenium.type( k, v )
        
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)