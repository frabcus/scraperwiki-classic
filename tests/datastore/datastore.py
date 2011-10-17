"""
Tests for the dataproxy/datastore/whatever that can test the common edge cases
and should exercise the python library at the same time.
"""
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
        settings = json.loads( open( os.path.join(os.path.dirname( __file__ ), "dev_test_settings.json") ).read() )
        scraperwiki.datastore.create( **settings )
        
    def tearDown(self):
        # Clean up after each run
        scraperwiki.datastore.close()
        
        
class ValidTests( DataStoreTester ):
    """
    Tests that we expect to succeed
    """
    
    def test_example(self):
        self.assertEqual('', '')



class InvalidTests( DataStoreTester ):
    """
    Tests that we expect to fail. These should succeed i.e. they should
    correctly identify that the tests failed.
    """
    
    def test_example(self):
        self.assertEqual('failed', 'failed')



if __name__ == '__main__':
    unittest.main()