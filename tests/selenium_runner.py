#!/usr/bin/env python

import sys, unittest, imp, optparse
from selenium_test import SeleniumTest
import simplejson as json

#   eg:
#
# python selenium_runner.py --url=http://dev.scraperwiki.com --seleniumhost=ondemand.saucelabs.com 
#           --username=goatchurch --accesskey=6727bb66-998e-464c-b8f1-bb4f31d1a531 --os="Windows 2003" 
#           --browser=firefox --browserversion=3.6.--tests=test_scrapers,test_scrapers

if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option("-u", "--url", dest="url", action="store", type='string',
                      help="URL of the ScraperWiki web application to test, defaults to http://localhost:8000/",  
                      default="http://localhost:8000/", metavar="application url (string)")

    parser.add_option("--tests", default="test_registration,test_scrapers", help="Comma separated list of modules to run tests from, defaults to 'test_registration,test_scrapers'")

    parser.add_option("-s", "--seleniumhost", dest="shost", action="store", type='string',
                      help="The host that Selenium RC is running on",  
                      default="localhost", metavar="selenium host (string)")
    parser.add_option("-p", "--seleniumport", dest="sport", action="store", type='int',
                      help="The port that Selenium RC is running on",  
                      default=4444, metavar="Selenium port")
    parser.add_option("--username", help="Login to Selenium RC, if needed")
    parser.add_option("--accesskey", help="Access control to Selenium RC, if needeed")
    parser.add_option("--os", help="Operating system to run browser on, passed to Selenium RC, optional")
    parser.add_option("--browser", default="*firefox", help="Which browser, e.g. *firefox, *chrome, *safari, *iexplore. Put in a bad value to see full list. Defaults to *firefox.")
    parser.add_option("--browserversion", help="Passed into selenium with browser parameter, optional")
    
    (options, args) = parser.parse_args()

    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    
    SeleniumTest._selenium_host = options.shost
    SeleniumTest._selenium_port = options.sport
    SeleniumTest._app_url = options.url

    if options.username and options.accesskey and options.os and options.browser and options.browserversion:
        SeleniumTest._selenium_browser = json.dumps({ "username":options.username, "access-key":options.accesskey, 
                                                      "os":options.os, "browser":options.browser, "browser-version":options.browserversion })
    else:
        SeleniumTest._selenium_browser = options.browser
    print "SeleniumRC %s:%d, ScraperWiki %s, Browser %s" % (SeleniumTest._selenium_host, SeleniumTest._selenium_port, SeleniumTest._app_url, str(SeleniumTest._selenium_browser))

    if 'localhost' in options.url:
        print '*' * 80
        print 'If running tests locally, make sure that seleniumrc is running along with the\n\
    local services inside the virtualenv'
        print '*' * 80
        
    for testsmodule in options.tests.split(","):
        module = imp.load_module(testsmodule, *imp.find_module(testsmodule))
        print '\n%s\nRunning tests from module: %s\n' % ("="*80,repr(module))
        loader = unittest.TestLoader().loadTestsFromModule( module )
        unittest.TextTestRunner( verbosity=2 ).run( loader )
    
    
    
