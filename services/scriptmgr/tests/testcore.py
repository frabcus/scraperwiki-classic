#!/usr/bin/env python
# tests/testcore.py

"""Tests the core functionality of scriptmgr.

Assumes scriptmgr is already running."""

# http://docs.python.org/release/2.6.7/library/json.html
import json
# http://docs.python.org/release/2.6.7/library/unittest.html
import unittest
# http://docs.python.org/release/2.6.7/library/urllib.html
import urllib

import testbase

class testCore(testbase.testBase):

    def testAlive(self):
        """Should check scriptmgr is already running."""
        
        """
        If this fails then
        it may be that scriptmgr is not running already; which
        it should be to run the tests.
        """
        urllib.urlopen(self.URL("Status")).read()
        pass
    
    def testPython(self):
        """Should be able to run Python code."""
        stuff = self.Execute(
          """print 'hell'+'o'*3""", language='python')
        output = testbase.console(stuff)
        assert 'hellooo' in output

    def testCPUPython(self):
        """Should be able to catch CPU Exception (in Python)."""

        # This test intentionally takes a few seconds to run.

        # code is originally from
        # https://scraperwiki.com/scrapers/cpu-py_1/edit/
        code = """
import resource
import sys

# We artificially lower the soft CPU limit to 2 seconds, so that we
# run this scraper and see the exception in reasonable time.
resource.setrlimit(resource.RLIMIT_CPU, (2, 4))

# A loop that consumes CPU
a=2
try:
    while True:
        print a
        a = a*a
except Exception as e:
    if 'CPU' in str(e):
        print "CPU exception caught"
    else:
        print "Error, unexpected exception"
"""

        stuff = self.Execute(code)
        output = testbase.console(stuff)
        assert 'CPU exception' in output
