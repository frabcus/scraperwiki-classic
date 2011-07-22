#!/usr/bin/env python

import sys, unittest, imp, optparse, time
from selenium_test import SeleniumTest
import simplejson as json

# This is a copy of unittest.TextTestRunner, that adds extra option of pausing
# whenever there is an error. It uses _WritelnDecorator and _TextTestResult
# from unittest, which might cause problems with future versions of Python.
# (if so easiest thing may be to copy them from older verisons)
class OurTextTestRunner:
    """A test runner class that displays results in textual form.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    def __init__(self, stream=sys.stderr, descriptions=1, verbosity=1):
        self.stream = unittest._WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity

    def _makeResult(self):
        return unittest._TextTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()
        if not result.wasSuccessful():
            self.stream.write("FAILED (")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                self.stream.write("failures=%d" % failed)
            if errored:
                if failed: self.stream.write(", ")
                self.stream.write("errors=%d" % errored)
            self.stream.writeln(")")
        else:
            self.stream.writeln("OK")
        return result


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

    parser.add_option("--tests", default="test_registration,test_scrapers", 
                     help="Comma separated list of modules to run tests from, defaults to 'test_registration,test_scrapers'")
    parser.add_option("--verbosity", dest="verbosity", action="store", default=1, type='int', 
                     help="How much to display while running the tests, try 0, 1, 2. Default is 1.")

    parser.add_option("-s", "--seleniumhost", dest="shost", action="store", type='string',
                      help="The host that Selenium RC is running on",  
                      default="localhost", metavar="selenium host (string)")
    parser.add_option("-p", "--seleniumport", dest="sport", action="store", type='int',
                      help="The port that Selenium RC is running on",  
                      default=4444, metavar="Selenium port")
    parser.add_option("--username", help="Login to Selenium RC, if needed")
    parser.add_option("--accesskey", help="Access control to Selenium RC, if needeed")
    parser.add_option("--os", help="Operating system to run browser on, passed to Selenium RC, optional")
    parser.add_option("--browser", default="*firefox", 
                      help="Which browser, e.g. *firefox, *chrome, *safari, *iexplore. Put in a bad value to see full list. Defaults to *firefox.")
    parser.add_option("--browserversion", help="Passed into selenium with browser parameter, optional")
    
    (options, args) = parser.parse_args()

    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    
    SeleniumTest._selenium_host = options.shost
    SeleniumTest._selenium_port = options.sport
    SeleniumTest._app_url = options.url
    SeleniumTest._verbosity = options.verbosity

    if options.username and options.accesskey and options.os and options.browser and options.browserversion:
        SeleniumTest._selenium_browser = json.dumps({ "username":options.username, "access-key":options.accesskey, 
                                                      "os":options.os, "browser":options.browser, "browser-version":options.browserversion })
    else:
        SeleniumTest._selenium_browser = options.browser

    if options.verbosity > 1:
        print "SeleniumRC %s:%d, ScraperWiki %s, Browser %s" % (SeleniumTest._selenium_host, SeleniumTest._selenium_port, SeleniumTest._app_url, str(SeleniumTest._selenium_browser))
        if 'localhost' in options.url:
            print '*' * 80
            print 'If running tests locally, make sure that seleniumrc is running along with the\n\
        local services inside the virtualenv'
            print '*' * 80
        
    for testsmodule in options.tests.split(","):
        module = imp.load_module(testsmodule, *imp.find_module(testsmodule))
        if options.verbosity > 1:
            print '\n%s\nRunning tests from module: %s\n' % ("="*80,module.__name__)
        elif options.verbosity > 0:
            print 'module %s' % (module.__name__)
        loader = unittest.TestLoader().loadTestsFromModule( module )
        OurTextTestRunner( verbosity=options.verbosity ).run( loader )
    
    
    
