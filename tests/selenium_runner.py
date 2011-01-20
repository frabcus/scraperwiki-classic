import sys,unittest

from selenium_test import SeleniumTest
from test_registration import TestRegistration
from test_scrapers import TestScrapers


if __name__ == '__main__':
    
    module = sys.modules[ globals()['__name__'] ]
    loader = unittest.TestLoader().loadTestsFromModule( module )
    print 'Test cases loaded from current module - %s' % repr(module)        

    unittest.TextTestRunner( verbosity=2 ).run( loader )
    print SeleniumTest._valid_username
    print SeleniumTest._valid_password    