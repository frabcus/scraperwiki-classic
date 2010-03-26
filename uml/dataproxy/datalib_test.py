#!/usr/bin/python

import  sys
import  string
import  time
import  unittest
import  datalib

datalib.dbtype = 'sqlite3'

USAGE       = '[--skipTest=test1,test2,...] [--onlyTest=test1,test2,...]'
onlyTest   = None
skipTest   = None

class TestOf_datalib (unittest.TestCase) :

    def setUp (self) :

        fd = open('db.sq3', 'w')
        fd.write(open('db_init.sq3', 'r').read())
        fd.close ()
        assert datalib.connection('config.test') is not None

    def tearDown (self) :

        datalib.db = None

    def test_fixPlaceHolder (self) :

        assert datalib.fixPlaceHolder ("%s") == "?"

    def test_fixKVKey (self) :

        assert datalib.fixKVKey ('a b') == 'a_b'

    def test_uniqueHash (self) :

        assert datalib.uniqueHash ([ 'k1', 'k2' ],  { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V1' }) == '76f2457e36fcf2eae546021a93cbf120'

    def test_save1 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1', 'k2' ], { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V1' })
        assert rc
        assert arg == 'Data record inserted'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select unique_hash  from items where `item_id` = %s', (seq,)).fetchone()[0] == '76f2457e36fcf2eae546021a93cbf120'
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 3
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('k2',)).fetchone()[0] == 'K2'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V1'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save2 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2001-01-01', '123456')
        assert rc
        assert arg == 'Data record inserted'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] == '123456'
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == '2001-01-01'
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 2
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V1'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save3 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1', 'k2' ], { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V1' })
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.save ('__scraperid__', [ 'k1', 'k2' ], { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V1' })
        assert rc
        assert arg == 'Data record already exists'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select unique_hash  from items where `item_id` = %s', (seq,)).fetchone()[0] == '76f2457e36fcf2eae546021a93cbf120'
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 3
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('k2',)).fetchone()[0] == 'K2'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V1'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save4 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1', 'k2' ], { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V1' })
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.save ('__scraperid__', [ 'k1', 'k2' ], { 'k1' : 'K1', 'k2' : 'K2', 'v1' : 'V9' })
        assert rc
        assert arg == 'Data record updated'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select unique_hash  from items where `item_id` = %s', (seq,)).fetchone()[0] == '76f2457e36fcf2eae546021a93cbf120'
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 3
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('k2',)).fetchone()[0] == 'K2'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V9'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save6 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2001-01-01', '123456')
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.save ('__scraperid__', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2001-02-02', '654321')
        assert rc
        assert arg == 'Data record already exists'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] == '654321'
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == '2001-02-02'
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 2
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V1'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save7 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V1' }, '2001-01-01', '123456')
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.save ('__scraperid__', [ 'k1' ], { 'k1' : 'K1', 'v1' : 'V9' }, '2001-02-02', '654321')
        assert rc
        assert arg == 'Data record updated'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] == '654321'
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == '2001-02-02'
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 2
        assert datalib.execute ('select value   from kv where key = %s', ('k1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('v1',)).fetchone()[0] == 'V9'
        assert datalib.execute ('select item_id from kv where key = %s', ('k1',)).fetchone()[0] == seq

    def test_save8 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'K1', 'k 2' : 'K2', 'v 1' : 'V1' })
        assert rc
        assert arg == 'Data record inserted'
        seq = datalib.execute  ('select id from sequences').fetchone()[0]
        assert datalib.execute ('select count(*) from items').fetchone()[0] == 1
        assert datalib.execute ('select unique_hash  from items where `item_id` = %s', (seq,)).fetchone()[0] == '1bcb62e0e41068ea905762737b7186b4'
        assert datalib.execute ('select scraper_id   from items where `item_id` = %s', (seq,)).fetchone()[0] == '__scraperid__'
        assert datalib.execute ('select date_scraped from items where `item_id` = %s', (seq,)).fetchone()[0][:10] == time.strftime ('%Y-%m-%d')
        assert datalib.execute ('select latlng       from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select date         from items where `item_id` = %s', (seq,)).fetchone()[0] is None
        assert datalib.execute ('select count(*) from kv').fetchone()[0] == 3
        assert datalib.execute ('select value   from kv where key = %s', ('k_1',)).fetchone()[0] == 'K1'
        assert datalib.execute ('select value   from kv where key = %s', ('k_2',)).fetchone()[0] == 'K2'
        assert datalib.execute ('select value   from kv where key = %s', ('v_1',)).fetchone()[0] == 'V1'
        assert datalib.execute ('select item_id from kv where key = %s', ('k_1',)).fetchone()[0] == seq

    def test_fetch1 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'K1', 'k 2' : 'K2', 'v 1' : 'V1' })
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.fetch('__scraperid__', { 'k 1' : 'K1', 'k 2' : 'K2' })
        assert rc
        assert len(arg) == 1
        assert arg[0]['date'  ] is None
        assert arg[0]['latlng'] is None
        assert arg[0]['data'  ][u'k_1'] == u'K1'
        assert arg[0]['data'  ][u'k_2'] == u'K2'
        assert arg[0]['data'  ][u'v_1'] == u'V1'

    def test_fetch2 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'K1', 'k 2' : 'K2', 'v 1' : 'V1' })
        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'L1', 'k 2' : 'L2', 'v 1' : 'W1' })
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.fetch('__scraperid__', { 'k 1' : 'L1', 'k 2' : 'L2' })
        assert rc
        assert len(arg) == 1
        assert arg[0]['date'  ] is None
        assert arg[0]['latlng'] is None
        assert arg[0]['data'  ][u'k_1'] == u'L1'
        assert arg[0]['data'  ][u'k_2'] == u'L2'
        assert arg[0]['data'  ][u'v_1'] == u'W1'

    def test_fetch3 (self) :

        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'K1', 'k 2' : 'K2', 'v 1' : 'V1' })
        rc, arg = datalib.save ('__scraperid__', [ 'k 1', 'k 2' ], { 'k 1' : 'L1', 'k 2' : 'L2', 'v 1' : 'W1' })
        assert rc
        assert arg == 'Data record inserted'
        rc, arg = datalib.fetch('__scraperid__', {})
        assert rc
        assert len(arg) == 2
        assert arg[0]['date'  ] is None
        assert arg[0]['latlng'] is None
        assert arg[0]['data'  ][u'k_1'] == u'K1'
        assert arg[0]['data'  ][u'k_2'] == u'K2'
        assert arg[0]['data'  ][u'v_1'] == u'V1'
        assert arg[1]['date'  ] is None
        assert arg[1]['latlng'] is None
        assert arg[1]['data'  ][u'k_1'] == u'L1'
        assert arg[1]['data'  ][u'k_2'] == u'L2'
        assert arg[1]['data'  ][u'v_1'] == u'W1'

def testSuite () :

    ts = unittest.TestSuite ()
    tp = 'test_'
    for key in TestOf_datalib.__dict__.keys() :
        if key[:len(tp)] == tp :
            if onlyTest is not None and not key in onlyTest :
                continue
            if skipTest is not None and     key in skipTest :
                continue
            print key
            ts.addTest (TestOf_datalib(key))

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
