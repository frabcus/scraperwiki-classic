#!/usr/bin/env python
# ScraperWiki Limited
# David Jones, 2011-11-28

"""
Tests for the dataproxy/datastore/whatever that can test the common edge cases
and should exercise the python library at the same time.
"""

import json
import os
import sys
import uuid
import unittest

sys.path.append(os.path.abspath( os.path.join(os.path.abspath(__file__), '../../../scraperlibs/python/')))
try:
    import scraperwiki
except Exception, e:
    print '*' * 80    
    print '* Make sure the folder containing scraperlibs/python is in your $PYTHONPATH'
    print '* Suggest:',  os.path.abspath( os.path.join(os.path.abspath(__file__), '../../../scraperlibs/python/'))
    print '*' * 80
    print e
    sys.exit(0)

resource_dir = None

def title(s):
    print '\n%s' % s
    print '-' * len(s)

def cleanup(name):
    p = os.path.join(resource_dir,name)
    try:
        os.unlink( os.path.join(p, 'defaultdb.sqlite'))
        os.rmdir( p )
    except:
        pass    

def update_settings_for_name(settings,name):
    import hashlib
    secret_key = '%s%s' % (name, settings['secret'],)
    settings['verification_key'] = hashlib.sha256(secret_key).hexdigest()  
    del settings['secret']


##############################################################################
#
# Tests - Start of the tests, all should extend DataStoreTester so that setUp
# and tearDown happen correctly.
#        
##############################################################################

def our_settings():
    """Return a JSON object (that is, a dict) of the settings used for
    the test.  These are stored in the file "dev_test_settings.json".
    """

    return json.load(
      open(os.path.join(os.path.dirname(__file__),
                        "dev_test_settings.json")))


class DataStoreTester(unittest.TestCase):
    """
    Create a datastore connection for the tests to use
    """
    def setUp(self):
        scraperwiki.logfd = sys.stdout
        self.settings = our_settings()
        self.settings['scrapername'], self.settings['runid'] = self.random_details()
        update_settings_for_name(self.settings,self.settings['scrapername'])
        scraperwiki.datastore.create( **self.settings )
        
    def random_details(self):
        return 'x_' + str(uuid.uuid4()), str(uuid.uuid4()), 
        
    def tearDown(self):
        global resource_dir
        if resource_dir:
            cleanup(self.settings['scrapername'])
        else:
            print 'Should delete the resourcedir directory called %s' % self.settings['scrapername']
        scraperwiki.datastore.close()
        
        
        
class BasicDataProxyTests( DataStoreTester ):
    """
    Basic tests that the data proxy is working and allowing us to query data
    """
    
    def test_simple_create_and_check(self):
        title('test_simple_create_and_check')
        # Check we can save and get the right count back
        scraperwiki.sqlite.save(['id'], {'id':1})
        x = scraperwiki.sqlite.execute('select count(*) from swdata')
        self.assertEqual( x['data'][0][0], 1)
        
        
    def test_simple_create_and_check_custom_table(self):
        title('test_simple_create_and_check_custom_table')
        # Check we can save to a named table and get the right count back        
        scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test table')
        x = scraperwiki.sqlite.execute('select count(*) from `test table`')
        self.assertEqual( x['data'][0][0], 1)        


    def test_simple_create_and_check_custom_table_fail(self):
        title('test_simple_create_and_check_custom_table_fail')
        # Check we can save to a named table and failed to get data back when 
        # we access swdata
        scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test table')
        try:
            x = scraperwiki.sqlite.execute('select count(*) from `swdata`')
            self.fail("Found the custom table magically")
        except AssertionError, e:
            self.fail(e)
        except:
            pass # We expect an error so we can ignore it
        

    def test_attach_denied(self):
        title('test_attach')
        settings = our_settings()
        settings['scrapername'], settings['runid'] = self.random_details()
        update_settings_for_name(settings,settings['scrapername'])        
        attach_to = settings['scrapername']
        scraperwiki.datastore.create( **settings )
        print scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test')
        scraperwiki.datastore.close()

        settings = our_settings()
        settings['scrapername'], settings['runid'] = self.random_details()
        update_settings_for_name(settings,settings['scrapername'])       
        scraperwiki.datastore.create( **settings )
        scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test')
        try:
            scraperwiki.sqlite.attach(attach_to,attach_to)         
            scraperwiki.sqlite.select('* from `%s`.test' % attach_to)
        except Exception, e:
            # We expect to fail here so if we succeeded then we should fail
            self.fail(e)
        cleanup(attach_to)

    def test_create_download_sqlite(self):
        import base64
        
        title('test_create_download_sqlite')
        scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test table')
        initsqlitedata = scraperwiki.datastore.request({"maincommand":"sqlitecommand", "command":"downloadsqlitefile", "seek":0, "length":0})
        if "filesize" not in initsqlitedata:
            print str(initsqlitedata)
            return
        filesize = initsqlitedata['filesize']         
        size = 0
        memblock=100000
        for offset in range(0, filesize, memblock):
            sqlitedata = scraperwiki.datastore.request({"maincommand":"sqlitecommand", "command":"downloadsqlitefile", "seek":offset, "length":memblock})
            content = sqlitedata.get("content")
            if sqlitedata.get("encoding") == "base64":
                content = base64.decodestring(content)            
            print len(content), sqlitedata.get("length")
            self.failUnless( len(content) == sqlitedata.get("length") )
        
        
    def test_create_download_csv(self):
        pass

        
##############################################################################
#
# Main - see if we can guess where the resourcedir is and warn the user, so 
# they can check as we will be deleting folders. May be better to check that
# we are running in dev.
#        
##############################################################################

if __name__ == '__main__':
    p = os.path.abspath(__file__)
    p = os.path.abspath( os.path.join(p, '../../../resourcedir/') )
    if os.path.exists(p):
        resource_dir = p
        print ''
        print '*' * 80
        print 'Guessed that resourcedir is %s \nand created folders will be deleted from there.' % resource_dir
        print '\nIs this okay?'
        s = raw_input('[y/N]--> ')
        if not s or s.lower() != 'y':
            sys.exit(0)
        print '\nRunning tests'
        print '=' * 13
    unittest.main()
