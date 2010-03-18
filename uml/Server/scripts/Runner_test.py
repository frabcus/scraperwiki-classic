#!/usr/bin/python

import	sys
import	unittest
import	Runner
import	re
import	os
import	string
import	time
import	StringIO

USAGE	   = ' [--skipTest=test1,test2,...] [--onlyTest=test1,test2,...]'
onlyTest   = None
skipTest   = None


class TestOf_Runner (unittest.TestCase) :

    def setUp (self) :

        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout  = StringIO.StringIO()
        sys.stderr  = StringIO.StringIO()

    def tearDown (self) :

        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def execute (self, script) :

        Runner.execute (script, 0)
        self.m_text = sys.stdout.getvalue()

    def search (self, pattern) :

        self.assertTrue (re.search (pattern, self.m_text, re.DOTALL), self.m_text)

    def typeContent (self, type, content) :

        self.search (r'"content": "%s"' % content)
        self.search (r'"message_type": "%s"' % type)

    def test_Runner_1 (self) :

        self.execute     ("print 1\nprint 2\nprint 3\n")
        self.typeContent ('console', r'1\\n')
        self.typeContent ('console', r'2\\n')
        self.typeContent ('console', r'3\\n')

    def test_Runner_2 (self) :

        self.execute 	 ("x = 0\ny = 0\nz = x / y\n")
        self.typeContent ('exception', r"&lt;type 'exceptions.ZeroDivisionError'&gt;")

    def test_Runner_3 (self) :

        self.execute 	 ("for i in range(10) : print i\n")
        self.typeContent ('console', r'0\\n')
        self.typeContent ('console', r'1\\n')
        self.typeContent ('console', r'2\\n')
        self.typeContent ('console', r'3\\n')
        self.typeContent ('console', r'4\\n')
        self.typeContent ('console', r'5\\n')
        self.typeContent ('console', r'6\\n')
        self.typeContent ('console', r'7\\n')
        self.typeContent ('console', r'8\\n')
        self.typeContent ('console', r'9\\n')

    def test_Runner_4 (self) :

        self.execute 	 ("for i in range(10) : print i,\n")
        self.typeContent ('console', r'0 1 2 3 4 5 6 7 8 9')



def testSuite () :

    ts = unittest.TestSuite ()
    tp = 'test_'
    for key in TestOf_Runner.__dict__.keys() :
        if key[:len(tp)] == tp :
            if onlyTest is not None and not key in onlyTest :
                continue
            if skipTest is not None and     key in skipTest :
                continue
            print key
            ts.addTest (TestOf_Runner(key))

    return ts


if __name__ == "__main__" :

    for arg in sys.argv[1:] :
        if arg[:11] == '--onlyTest='	:
            onlyTest   = string.split(arg[11:], ',')
            continue
        if arg[:11] == '--skipTest='	:
            skipest   = string.split(arg[11:], ',')
            continue
        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)

    runner = unittest.TextTestRunner(sys.stdout)
    runner.run(testSuite())
