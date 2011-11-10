"""
Tests for the dataproxy/datastore/whatever that can test the common edge cases
and should exercise the python library at the same time.
"""
import uuid
import os, sys
import unittest
import json
try:
    import scraperwiki
except Exception, e:
    print '*' * 80
    print '* Make sure the folder containing scraperlibs/python is in your $PYTHONPATH'
    print '*' * 80
    print e
    sys.exit(0)

resource_dir = None

def update_settings_for_name(settings,name):
    import hashlib
    secret_key = '%s%s' % (name, settings['secret'],)
    settings['verification_key'] = hashlib.sha256(secret_key).hexdigest()  
    del settings['secret']


class DataStoreTester(unittest.TestCase):
    """
    Create a datastore connection for the tests to use
    """
    def setUp(self):
        scraperwiki.logfd = sys.stdout
        self.settings = json.loads( open( os.path.join(os.path.dirname( __file__ ), "dev_test_settings.json") ).read() )        
        self.settings['scrapername'], self.settings['runid'] = self.random_details()
        update_settings_for_name(self.settings,self.settings['scrapername'])
        scraperwiki.datastore.create( **self.settings )
        
    def random_details(self):
        return 'x_' + str(uuid.uuid4()), str(uuid.uuid4()), 
        
    def tearDown(self):
        global resource_dir
        if resource_dir:
            p = os.path.join(resource_dir, self.settings['scrapername'])
            print 'Going to delete %s because you said so' % p
            try:
                os.unlink( os.path.join(p, 'defaultdb.sqlite'))
                os.rmdir( p )
                print "It's gone"            
            except:
                pass
        else:
            print 'Should delete the resourcedir directory called %s' % self.settings['scrapername']
        scraperwiki.datastore.close()
        
        
        
class BasicDataProxyTests( DataStoreTester ):
    """
    
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
        

    def test_attach(self):
        title('test_attach')
        settings = json.loads( open( os.path.join(os.path.dirname( __file__ ), "dev_test_settings.json") ).read() )        
        settings['scrapername'], settings['runid'] = self.random_details()
        update_settings_for_name(settings,settings['scrapername'])        
        attach_to = settings['scrapername']
        scraperwiki.datastore.create( **settings )
        # Save to the attachable database
        scraperwiki.sqlite.save(['id'], {'id':1}, table_name='test')
        scraperwiki.datastore.close()

        settings = json.loads( open( os.path.join(os.path.dirname( __file__ ), "dev_test_settings.json") ).read() )                
        settings['scrapername'], settings['runid'] = self.random_details()
        update_settings_for_name(settings,settings['scrapername'])                
        scraperwiki.datastore.create( **settings )
        print scraperwiki.sqlite.select('* from `%s`.test' % attach_to)
        
        
def title(s):
    print '\n%s' % s
    print '-' * len(s)
    
        

if __name__ == '__main__':
    p = os.path.abspath(__file__)
    p = os.path.abspath( os.path.join(p, '../../../resourcedir/') )
    if os.path.exists(p):
        resource_dir = p
        print 'Your RESOURCEDIR is set to %s and created folders will be deleted from there.' % resource_dir
        print 'Is this okay?'
        s = raw_input('[y/N]--> ')
        if not s or s.lower() != 'y':
            sys.exit(0)
        print '\nRunning tests'
        print '=' * 13
    unittest.main()
