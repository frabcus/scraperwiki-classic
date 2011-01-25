import sys,unittest

from selenium_test import SeleniumTest
from optparse import OptionParser

from test_registration import TestRegistration
from test_scrapers import TestScrapers

if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option("-s", "--seleniumhost", dest="shost", action="store", type='string',
                      help="The host that Selenium RC is running on",  
                      default="localhost", metavar="selenium host (string)")
    parser.add_option("-p", "--seleniumport", dest="sport", action="store", type='int',
                      help="The port that Selenium RC is running on",  
                      default=4444, metavar="Selenium port")
    parser.add_option("-u", "--url", dest="url", action="store", type='string',
                      help="The application url",  
                      default="http://localhost:8000/", metavar="application url (string)")


    (options, args) = parser.parse_args()
    SeleniumTest._selenium_host = options.shost
    SeleniumTest._selenium_port = options.sport
    SeleniumTest._app_url = options.url
        
    module = sys.modules[ globals()['__name__'] ]
    loader = unittest.TestLoader().loadTestsFromModule( module )
    print 'Test cases loaded from current module - %s' % repr(module)        

    unittest.TextTestRunner( verbosity=2 ).run( loader )
