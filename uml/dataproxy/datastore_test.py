#!/usr/bin/python

import  sys
import  string
import  time
import  unittest
import  datetime
import  datastore

USAGE       = '[--skipTest=test1,test2,...] [--onlyTest=test1,test2,...]'
onlyTest   = None
skipTest   = None

def nullConnect (self, conf) :

    pass

def nullRequest (self, req) :

    return [ True, req]

realConnect                         = datastore.DataStoreClass.connect
realRequest                         = datastore.DataStoreClass.request
datastore.DataStoreClass.connect    = nullConnect
datastore.DataStoreClass.request    = nullRequest

class TestOf_datastore (unittest.TestCase) :

    def setUp (self) :

        pass

    def tearDown (self) :

        datastore.ds = None

    def test_save1 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' })
        assert rc
        assert arg == ('save', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, None, None)

    def test_SaveDate1 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, date = datetime.datetime(2010, 1, 1))
        assert rc
        assert arg == ('save', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2010-01-01 00:00:00', None)

    def test_SaveDate2 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, date = datetime.date    (2010, 1, 1))
        assert rc
        assert arg == ('save', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2010-01-01', None)

    def test_SaveDate4 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, date = '2010-01-01')
        assert not rc
        assert arg == "date should be a python.datetime (not <type 'str'>)"

    def test_SaveLatLng1 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, latlng = (1,2))
        assert rc
        assert arg == ('save', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, None, '001.000000,002.000000')

    def test_SaveLatLng2 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, latlng = (1.1,2.2))
        assert rc
        assert arg == ('save', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, None, '001.100000,002.200000')

    def test_SaveLatLng3 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, latlng = (1,2,3))
        assert not rc
        assert arg == 'latlng must be a (float,float) list or tuple'

    def test_SaveLatLng4 (self) :

        ds = datastore.DataStore(None)
        rc, arg = ds.save ([ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, latlng = ('1','2'))
        assert not rc
        assert arg == 'latlng must be a (float,float) list or tuple'

def testSuite () :

    ts = unittest.TestSuite ()
    tp = 'test_'
    for key in TestOf_datastore.__dict__.keys() :
        if key[:len(tp)] == tp :
            if onlyTest is not None and not key in onlyTest :
                continue
            if skipTest is not None and     key in skipTest :
                continue
            print key
            ts.addTest (TestOf_datastore(key))

    return ts


if __name__ == "__main__" :

    for arg in sys.argv[1:] :
        if arg[:11] == '--onlyTest='    :
            onlyTest   = string.split(arg[11:], ',')
            continue
        if arg[:11] == '--skipTest='    :
            skipest   = string.split(arg[11:], ',')
            continue
        print "usage: " + sys.argv[0] + USAGE
        sys.exit (1)

    runner = unittest.TextTestRunner(sys.stdout)
    runner.run(testSuite())
