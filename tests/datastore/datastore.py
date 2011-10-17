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
except:
    print '*' * 80
    print 'Make sure the folder containing scraperlibs/python is in your $PYTHONPATH'
    print '*' * 80
    sys.exit(0)


class DataStoreTester(unittest.TestCase):
    """
    Create a datastore connection for the tests to use
    """

    def setUp(self):
        scraperwiki.logfd = sys.stdout
        self.settings = json.loads( open( os.path.join(os.path.dirname( __file__ ), "dev_test_settings.json") ).read() )        
        self.settings['scrapername'], self.settings['runid'] = self.random_details()
        
        scraperwiki.datastore.create( **self.settings )
        
    def random_details(self):
        return 'x_' + str(uuid.uuid4()), str(uuid.uuid4()), 
        
    def tearDown(self):
        # Clean up after each run
        scraperwiki.datastore.close()
        
        
class ValidTests( DataStoreTester ):
            
    def test_simple_create(self):
        scraperwiki.sqlite.save(['id'], {'id':1})


class InvalidTests( DataStoreTester ):
    """
    Tests that we expect to fail. These should succeed i.e. they should
    correctly identify that the tests failed.
    """
    
    def test_example(self):
        scraperwiki.datastore.create( **self.settings )        
        self.assertEqual('failed', 'failed')



if __name__ == '__main__':
    unittest.main()