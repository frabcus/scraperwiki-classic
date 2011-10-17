import unittest


class TestDataStore(unittest.TestCase):

    def setUp(self):
        # Load datastore settings for this run.
        self.something = ''
        
    def tearDown(self):
        # Clean up after each run
        pass

    def test_example(self):
        self.assertEqual(self.something, '')




if __name__ == '__main__':
    unittest.main()