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
