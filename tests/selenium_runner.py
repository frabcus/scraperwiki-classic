import sys,unittest

from test_registration import TestRegistration


if __name__ == '__main__':
    module = sys.modules[ globals()['__name__'] ]
    loader = unittest.TestLoader().loadTestsFromModule( module )
    print 'Test cases loaded from current module - %s' % repr(module)        

    unittest.TextTestRunner( verbosity=2 ).run( loader )
