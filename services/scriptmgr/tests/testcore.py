#!/usr/bin/env python
# tests/core.py

"""Tests the core functionality of scriptmgr."""

# http://docs.python.org/release/2.6.7/library/json.html
import json
# http://docs.python.org/release/2.6.7/library/unittest.html
import unittest
# http://docs.python.org/release/2.6.7/library/urllib.html
import urllib

class testCore(unittest.TestCase):

    url = "http://127.0.0.1:9001/"

    def setUp(self):
        pass

    def Execute(self, code, language='python'):
        """Execute a script on the configured scriptmgr.
        Potentionally of some general use; could move.
        """

        # http://docs.python.org/release/2.6.7/library/uuid.html
        import uuid

        # A random UUID.
        id = str(uuid.uuid4())

        d = {
            "runid" : id,
            "code": code,
            "scrapername": "test",
            "scraperid": id,
            "language": language
        }
        body = json.dumps(d)
        u = urllib.urlopen(self.URL("Execute"), data=body)
        return u.read()

    def URL(self, command):
        """Form a URL to access the scriptmgr by prefixing with
        the configured self.url.  *command* will typically be "Status"
        or "Execute" and so on (see scriptmgr.js for details).
        """
        return self.url + command

    def testAlive(self):
        urllib.urlopen(self.URL("Status")).read()
        pass
    
    def testPython(self):
        self.Execute("""print 'hell'+'o'*3""", language='python')
        pass
