#!/usr/bin/env python
# tests/core.py

"""Tests the core functionality of scriptmgr."""

# http://docs.python.org/release/2.6.7/library/unittest.html
import unittest
# http://docs.python.org/release/2.6.7/library/urllib.html
import urllib

class testCore(unittest.TestCase):
    def setUp(self):
        self.url = "http://127.0.0.1:9001/"

    def URL(self, command):
        """Form a URL to access the scriptmgr by prefixing with
        the configured self.url.  *command* will typically be "Status"
        or "Execute" and so on (see scriptmgr.js for details).
        """
        return self.url + command

    def testAlive(self):
        urllib.urlopen(self.URL("Status")).read()
        pass
