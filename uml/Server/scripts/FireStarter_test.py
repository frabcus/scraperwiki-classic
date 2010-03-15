#!/usr/bin/python

import	sys
import	unittest
import	FireStarter
import	re
import	os
import	string
import	time

USAGE	   = ' [--allowedDir=name] [--skipTest=test1,test2,...] [--onlyTest=test1,test2,...] [--proxy=http://address:port] [--mysql=host,db,user,pwd]'
proxy	   = 'http://192.168.254.101:9002'
allowedDir = '.'
onlyTest   = None
skipTest   = None
mysqlInfo  = ( '212.84.75.28', 'scraperwiki_datastore_dev', 'datastore', 'niflheim' )

proxyTest = """
import os
import urllib2
os.environ['http_proxy'] = '%s'
req = urllib2.Request('http://scraperwiki.com/hello_world.html')
try    : req.add_header('x-scraperid', os.environ['SCRAPER_ID'])
except : pass
res = urllib2.urlopen(req)
print res.read()
print "PROXY_OK"
"""

scraperTest = """
import scraperwiki
scraperwiki.scrape ('http://scraperwiki.com/hello_world.html')
print "SCRAPE_OK"
"""

proxyTestException = """
def f1() :
    a.b = 1
def f2() :
    f1()
print "LINE1"
print "LINE2"
f2()
print "O0OPS"
"""

streamTest = """
for v in range(10) :
    print "%d:0123456789" % v
"""

streamTestSlow = """
import time
import sys
for v in range(10) :
    print "%d:0123456789" % v
    sys.stdout.flush()
    time.sleep (1)
"""

streamTestKill = """
import time
import sys
for v in range(100) :
    print "%d:0123456789" % v
    sys.stdout.flush()
    time.sleep (1)
"""

envTest = """
import os
print 'E1=%s' % os.environ['E1']
print 'E2=%s' % os.environ['E2']
"""

mysqlTest = """
try :
    import MySQLdb
    connection = MySQLdb.connect \
	(	host	= '%s',
		db	= '%s',
		user	= '%s',
		passwd	= '%s'
	)
    print "OK"
except :
    import sys
    print "FAILED:" + str(sys.exc_info())

"""

importMod  = """
try    :
    import %s
    print "%s:OK"
except :
    print "%s:Failed"
"""
importList = [ 'BeautifulSoup', 'lxml', 'html5lib', 'simplejson', 'json', 'mechanize' ]
importTest = ""
for i in importList :
    importTest += importMod % (i, i, i)

commandMod  = """
if os.path.exists ("%s") :
    print "%s:OK"
else :
    print "%s:Failed"
"""
commandList = [ '/bin/ls', '/usr/bin/pdftohtml' ]
commandTest = "import os\n"
for c in commandList :
    commandTest += commandMod % (c, c, c)


importErrorTest = """
import bozo
"""

class TestOf_FireStarter (unittest.TestCase) :

    def setUp (self) :

        pass

    def tearDown (self) :

#       import SWLogger
#       swl = SWLogger.SWLogger()
#       swl.setHost (mysqlInfo[0])
#       swl.connect ()
#       swl.clean   ('l_runid')
        pass

    def test_NoDispatcher (self) :

        """
        Point FireStarter at non-existant dispatcher and verify that
	execution fails on connction refused.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_NoDispatcher')
        fs.setDispatcher ('127.0.0.1:64000')
        res = fs.command ('date')
        self.assertTrue  (res is None)
        self.assertTrue  (re.search ('urlopen.*error.*111.*Connection refused', fs.error(), re.DOTALL))

    def test_Command_id_user (self) :

        """
        Send 'id -u' command to controller and verify that the result is
        zero (controller running as user root).
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_Command_id_user')
        res = fs.command ('id -u')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertEquals('0\n', res)

    def test_Command_id_user_nobody (self) :
        
        """
        Send 'id -u' command to controller to run as user 'nobody' and
        verify that the result is correct user ID.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_Command_id_user_nobody')
        fs.setUser       ('nobody')
        res = fs.command ('id -u')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertEquals('65534\n', res)

    def test_Command_id_group (self) :
        
        """
        Send 'id -g' command to controller and verify that the result is
        zero (controller running as group root).
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_Command_id_group')
        res = fs.command ('id -g')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertEquals('0\n', res)

    def test_Command_id_group_daemon (self) :

        """
        Send 'id -u' command to controller to run as group 'daemon' and
        verify that the result is correct group ID.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_Command_id_group_daemon')
        fs.setGroup      ('daemon')
        res = fs.command ('id -g')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertEquals('1\n', res)

    def test_Execute (self) :

        """
        Execute a minimal python script in the UML instance and verify
        the expected result.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_Execute')
        res = fs.execute ('print "HELLO"\n')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
#       self.assertEquals('HELLO\n', res)
        self.assertTrue  (re.search ('HELLO\\\\n', res, re.DOTALL))

    def test_ASLimit (self) :

        """
        Execute script with active set. Script prints limit
        which is verified.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_CoreLimit')
        fs.setASLimit    (1024*1024*128)
        res = fs.execute ('import resource\nprint resource.getrlimit(resource.RLIMIT_AS)\n')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
#       self.assertEquals('(134217728L, 134217728L)\n', res)
        self.assertTrue  (re.search ('\\(134217728L, 134217728L\\)\\\\n', res, re.DOTALL))

    def test_CPULimit (self) :

        """
        Execute script with limited CPU time. Script prints CPU time limit
        which is verified.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_CPULimit')
        fs.setCPULimit   (16)
        res = fs.execute ('import resource\nprint resource.getrlimit(resource.RLIMIT_CPU)\n')
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertTrue  (re.search ('\\(16L, 16L\\)\\\\n', res, re.DOTALL))

#    def test_Allowed (self) :
#
#        """
#        Execute script with allowed sites. Verify that the dispatcher
#        has correctly written the allowed-sites file used by the proxy.
#        This test assumes the UML at 192.168.254.1 will be used.
#        """
#        fs  = FireStarter.FireStarter()
#        fs.setTestName     ('test_Allowed')
#        fs.setScraperID    ('test_allowed')
#        fs.addAllowedSites ('.*\.gov\.uk')
#        fs.addAllowedSites ('.*\.co\.uk')
#        res = fs.command   ('id -u', True)
#        self.assertTrue    (res is not None)
#        self.assertTrue    (fs.error() is None)
#        allow = open(allowedDir + '/' + fs.m_runID + '.list').readlines()
#        self.assertEquals  ('.*\.co\.uk\n',  allow[0])
#        self.assertEquals  ('.*\.gov\.uk\n', allow[1])

    def test_IPTables (self) :

        """
        Execute a command in a UML with an additional firewall rule. The
        command displays the firewall state; this is verified.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_IPTables')
        fs.addIPTables   ('-A OUTPUT -p tcp -d 192.168.1.66 --dport 9002 -j ACCEPT')
        res = fs.command ('iptables -L -n')
        self.assertTrue  (re.search ('OUTPUT.*ACCEPT.*192.168.0.0/16', 		res, re.DOTALL))
        self.assertTrue  (re.search ('OUTPUT.*ACCEPT.*192.168.1.66.*dpt:9002',	res, re.DOTALL))

    def test_Proxy (self) :

        """
        Execute a python script which sets the proxy and retrieves the
        scraperwiki home page. Verify some plausible text in the response.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName     ('test_Proxy')
        fs.setScraperID    ('test_proxy')
        fs.addAllowedSites ('.*\.com')
        fs.setTraceback    ('text')
        res = fs.execute   (proxyTest % proxy)
        self.assertTrue    (re.search ('Hello.*World', res, re.DOTALL))
        self.assertTrue    (re.search ('PROXY_OK',     res, re.DOTALL))

    def test_ProxyBlocked (self) :

        """
        Execute a python script which sets the proxy and retrieves a
        a blocked site.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName     ('test_Proxy')
        fs.setScraperID    ('test_proxy')
        fs.addBlockedSites ('scraperwiki.com')
        fs.addAllowedSites ('.*\.com')
        fs.setTraceback    ('text')
        try :
            res = fs.execute   (proxyTest % proxy)
        except FireStarter.FireError, e :
            res = str(e)
        self.assertTrue    (re.search ('"content": "HTTPError: Scraperwiki has blocked you from accessing',  res, re.DOTALL))

    def test_Scrape (self) :

        """
        Execute a python script which sets the proxy and retrieves the
        scraperwiki home page. Verify some plausible text in the response.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName     ('test_scrape')
        fs.setScraperID    ('test_scrape')
        fs.addAllowedSites ('.*\.com')
        fs.setEnvironment  ('http_proxy', proxy)
        fs.addPaths        ('/scraperwiki/dev/scraperlibs')
        res = fs.execute   (scraperTest)
        self.assertTrue    (re.search ('447 bytes from http://scraperwiki.com/hello_world.html', res, re.DOTALL))
        self.assertTrue    (re.search ('SCRAPE_OK',    res, re.DOTALL))

    def test_Stream (self) :

        """
        Execute a python script which returns several lines of data.
        Check that this can be read in multiple calls.
        """
        fs    = FireStarter.FireStarter()
        fs.setTestName     ('test_Stream')
        res   = fs.execute (streamTest, True)
        data  = ''
        bit   = res.read(10)
        while bit is not None and bit != '' :
            data += bit
            bit   = res.read(10) 
        lines = string.split (data, '\n')
        self.assertEquals (11, len(lines))
#       self.assertEquals ("0:0123456789", lines[ 0])
#       self.assertEquals ("9:0123456789", lines[ 9])
#       self.assertEquals ("",             lines[10])
        self.assertTrue   (re.search ('0:0123456789', lines[ 0], re.DOTALL))
        self.assertTrue   (re.search ('9:0123456789', lines[ 9], re.DOTALL))

    def test_StreamByLine (self) :

        """
        Execute a python script which returns several lines of data.
        Check that this can be read as separate lines.
        """
        fs    = FireStarter.FireStarter()
        fs.setTestName     ('test_StreamByLine')
        res   = fs.execute (streamTest, True)
        lines = []
        line  = res.readline()
        while line is not None and line != '' :
            lines.append (line)
            line  = res.readline()
        self.assertEquals (10, len(lines))
#       self.assertEquals ("0:0123456789\n", lines[ 0])
#       self.assertEquals ("9:0123456789\n", lines[ 9])
        self.assertTrue   (re.search ('0:0123456789', lines[ 0], re.DOTALL))
        self.assertTrue   (re.search ('9:0123456789', lines[ 9], re.DOTALL))

    def test_StreamByLineSlow (self) :

        """
        Execute a python script which returns several lines of data.
        Check that this can be read as separate lines.
        """
        fs    = FireStarter.FireStarter()
        fs.setTestName     ('test_StreamByLineSlow')
        fs.setScraperID    ('test_streambylineslow')
        res   = fs.execute (streamTestSlow, True)
        lines = []
        times = []
        line  = res.readline()
        while line is not None and line != '' :
            lines.append (line)
            times.append (time.time())
            line  = res.readline()
#       self.assertEquals ("0:0123456789\n", lines[ 0])
#       self.assertEquals ("9:0123456789\n", lines[ 9])
        self.assertEquals (10, len(lines))
        self.assertTrue   (re.search ('0:0123456789', lines[ 0], re.DOTALL))
        self.assertTrue   (re.search ('9:0123456789', lines[ 9], re.DOTALL))
        self.assertTrue	  (times[len(times)-1] > times[0] + 9)

    def test_ProxyException (self) :

        """
        Execute a python script which sets the proxy and retrieves the
        scraperwiki home page. Verify some plausible text in the response.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_ProxyException')
        fs.setTraceback  ('simple')
        res = None
        exc = None
#        try :
#            res = fs.execute (proxyTestException)
#        except FireStarter.FireError, e :
#            exc = str(e)
        exc = fs.execute (proxyTestException)
        self.assertTrue	  (string.find (exc, "Traceback (most recent call last):") >= 0)
        self.assertTrue   (string.find (exc, "Scraper, line 8, in <module>"      ) >= 0)
        self.assertTrue   (string.find (exc, "Scraper, line 5, in f2"            ) >= 0)
        self.assertTrue   (string.find (exc, "Scraper, line 3, in f1"            ) >= 0)
        self.assertTrue   (string.find (exc, "global name 'a' is not defined"    ) >= 0)

    def test_ProxyExceptionByLines (self) :

        """
        Execute a python script which sets the proxy and retrieves the
        scraperwiki home page. Verify some plausible text in the response.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_ProxyExceptionByLines')
        fs.setTraceback  ('text')
        exc = None
        res = fs.execute (proxyTestException, True)
        lines = []
#        try :
#            line  = res.readline()
#            while line is not None and line != '' :
#                lines.append (line)
#                line  = res.readline()
#        except FireStarter.FireError, e :
#            exc = str(e)
#        self.assertEquals (3, len(lines))
        line  = res.readline()
        while line is not None and line != '' :
            lines.append (line)
            line  = res.readline()
        exc = string.join (lines)
#       self.assertTrue	  (string.find (exc, "Traceback (most recent call last):") >= 0)
#       self.assertTrue   (string.find (exc, "Scraper, line 8, in <module>"      ) >= 0)
        self.assertTrue   (string.find (exc, "Scraper in f2"            ) >= 0)
        self.assertTrue   (string.find (exc, "Scraper in f1"            ) >= 0)
        self.assertTrue   (string.find (exc, "global name 'a' is not defined"    ) >= 0)

    def test_StreamKill (self) :

        """
        Execute a python script which returns several lines of data over
        a period of time but kill the connection early.
        """
        fs1    = FireStarter.FireStarter()
        fs1.setTestName       ('test_StreamKill_1')
        res1   = fs1.execute  (streamTestKill, True)
        line10 = res1.readline()
        line11 = res1.readline()
        line12 = res1.readline()
        del res1
        fs2    = FireStarter.FireStarter()
        fs2.setTestName       ('test_StreamKill_2')
        res2   = fs2.execute  (streamTestKill, True)
        line20 = res2.readline()
        line21 = res2.readline()
        line22 = res2.readline()
        del res2
#       self.assertEquals   ("0:0123456789\n", line10)
#       self.assertEquals   ("1:0123456789\n", line11)
#       self.assertEquals   ("0:0123456789\n", line20)
#       self.assertEquals   ("1:0123456789\n", line21)
        self.assertTrue     (re.search ('0:0123456789', line10, re.DOTALL))
        self.assertTrue     (re.search ('1:0123456789', line11, re.DOTALL))
        self.assertTrue     (re.search ('0:0123456789', line20, re.DOTALL))
        self.assertTrue     (re.search ('1:0123456789', line21, re.DOTALL))

    def test_addPaths (self) :

        """
        Check that paths are added correctly.
        """
        fs    = FireStarter.FireStarter()
        fs.addPaths ('P1', 'P2')

        headers = {}
        def setter (name, value) :
            headers[name] = value
        fs.setHeaders (setter)

        self.assertEquals ('P1', headers['x-paths-0'])
        self.assertEquals ('P2', headers['x-paths-1'])

    def test_addEnvironment (self) :

        """
        Check that environment values are added correctly.
        """
        fs    = FireStarter.FireStarter()
        fs.setEnvironment ('E1', 'e1')
        fs.setEnvironment ('E2', 'e2')

        headers = {}
        def setter (name, value) :
            headers[name] = value
        fs.setHeaders (setter)

        self.assertEquals ('E1=e1', headers['x-setenv-0'])
        self.assertEquals ('E2=e2', headers['x-setenv-1'])

    def test_addEnvironmentExec (self) :

        """
        Check that environment values are added correctly.
        """
        fs    = FireStarter.FireStarter()
        fs.setEnvironment  ('E1', 'e1')
        fs.setEnvironment  ('E2', 'e2')
        fs.setTestName     ('test_addEnvironmentExec')

        res = fs.execute   (envTest )
        self.assertTrue    (re.search ('E1=e1', res, re.DOTALL))
        self.assertTrue    (re.search ('E2=e2', res, re.DOTALL))

    def test_addEnvironmentCommand (self) :

        """
        Check that environment values are added correctly.
        """
        fs    = FireStarter.FireStarter()
        fs.setEnvironment  ('E1', 'e1')
        fs.setEnvironment  ('E2', 'e2')
        fs.setTestName     ('test_addEnvironmentCommand')

        res = fs.command   ('echo E1=$E1 E2=$E2')
        self.assertTrue    (re.search ('E1=e1', res, re.DOTALL))
        self.assertTrue    (re.search ('E2=e2', res, re.DOTALL))

    def test_setScraperID (self) :

        """
        Check that environment values are added correctly.
        """
        fs    = FireStarter.FireStarter()
        fs.setScraperID    ('test_setscraperid')
        fs.setTestName     ('test_setScraperID')

        res = fs.command   ('echo SID=$SCRAPER_GUID')
        self.assertTrue    (re.search ('SID=test_setscraperid', res, re.DOTALL))

    def test_import (self) :

        """
        Check that imports are available
        """
        fs    = FireStarter.FireStarter()
        fs.setTestName     ('test_import')
        res = fs.execute   (importTest )
        for i in importList :
            self.assertTrue (re.search ('%s:OK' % i, res, re.DOTALL), 'Import failed: %s' % i)

    def test_command (self) :

        """
        Check that commands are available
        """
        fs    = FireStarter.FireStarter()
        fs.setTestName     ('test_command')
        res = fs.execute   (commandTest )
        for c in commandList :
            self.assertTrue (re.search ('%s:OK' % c, res, re.DOTALL), 'Command failed: %s' % c)

    def test_Database (self) :

        """
        Execute a python script which connects to the database.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName     ('test_database')
        fs.setScraperID    ('test_database')
        fs.addIPTables     ('-A OUTPUT -p tcp -d 212.84.75.28 --dport 3306 -j ACCEPT')
        res = fs.execute   (mysqlTest % mysqlInfo)
        self.assertTrue    (re.search ('OK\\n', res, re.DOTALL))

    def test_loggerLocal (self) :

        import SWLogger
        swl = SWLogger.SWLogger()
        swl.setHost (mysqlInfo[0])
        swl.connect ()
        swl.log	    ('l_scraperid', 'l_runid', 'l_event', 'l_arg1')

    def test_Traceback_text (self) :

        code = 'x = 1\ny = 0\nz = x / y\n'
        try :
            import imp
            mod  = imp.new_module ('scraper')
            exec code in mod.__dict__
            res = None
        except :
            import TraceBack
            res = TraceBack.traceBack ('text', code, context = 10)
        self.assertEquals  ('Scraper', res[2])
        self.assertEquals  (3,         res[3])

    def test_Traceback_html (self) :

        code = 'x = 1\ny = 0\nz = x / y\n'
        try :
            import imp
            mod  = imp.new_module ('scraper')
            exec code in mod.__dict__
            res = None
        except :
            import TraceBack
            res = TraceBack.traceBack ('html', code, context = 10)
        self.assertEquals  ('Scraper', res[2])
        self.assertEquals  (3,         res[3])

    def test_ImportError (self) :

        """
        Execute a minimal python script in the UML instance and verify
        the expected result.
        """
        fs  = FireStarter.FireStarter()
        fs.setTestName   ('test_ImportError')
        res = fs.execute (importErrorTest)
        self.assertTrue  (res is not None)
        self.assertTrue  (fs.error() is None)
        self.assertTrue  (re.search ('"content": "Import failed: No module named bozo"', res, re.DOTALL))


def testSuite () :

    ts = unittest.TestSuite ()
    tp = 'test_'
    for key in TestOf_FireStarter.__dict__.keys() :
        if key[:len(tp)] == tp :
            if onlyTest is not None and not key in onlyTest :
                continue
            if skipTest is not None and     key in skipTest :
                continue
            print key
            ts.addTest (TestOf_FireStarter(key))

    return ts


if __name__ == "__main__" :

    for arg in sys.argv[1:] :
        if arg[: 8] == '--proxy='	:
            proxy = arg[8:]
            continue
        if arg[:13] == '--allowedDir='	:
            allowedDir = arg[13:]
            continue
        if arg[:11] == '--onlyTest='	:
            onlyTest   = string.split(arg[11:], ',')
            continue
        if arg[:11] == '--skipTest='	:
            skipest   = string.split(arg[11:], ',')
            continue
        if arg[: 8] == '--mysql='	:
            mysqlInfo  = tuple(arg[8:].split(','))
            continue
        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)

    runner = unittest.TextTestRunner(sys.stdout)
    runner.run(testSuite())
