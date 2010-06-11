require_once  'scraperwiki/datastore.php'         ;
print "GO\n" ;
sw_data_save (array('key'), array('key' => 'key_1', 'message' => 'HELLO_1')) ;
sw_data_save (array('key'), array('key' => 'key_2', 'message' => 'HELLO_2')) ;
print "OK\n" ;
