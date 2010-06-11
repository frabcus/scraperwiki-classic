<?php

class DataStoreClass
{
   private static $m_ds       ;
   protected      $m_socket   ;
   protected      $m_host     ;
   protected      $m_port     ;

   function __construct ($host, $port)
   {
      $this->m_socket    = null     ;
      $this->m_host      = $host    ;
      $this->m_port      = $port    ;
   }

   function mangleflattendict ($data)
   {
      $rdata = array() ;
      foreach ($data as $key => $value)
      {
         $rkey = str_replace (' ', '_', $key) ;
        
         if     (is_null($value) ) $rvalue  = ''  ;
         elseif ($value === true ) $rvalue  = '1' ; 
         elseif ($value === false) $rvalue  = '0' ;
         else                      $rvalue  = sprintf ("%s", $value) ;
            
         $rdata[$rkey] = $rvalue ;
      }
      return $rdata ;
   }

   function mangleflattenkeys ($keys)
   {
      $rkeys = array() ;
      foreach ($keys as $key)
      {
         $rkey = str_replace (' ', '_', $key) ;
         $rkeys[] = $rkey ;
      }
      return $rkeys ;
   }

   function connect ()
   {
      /*
      Connect to the data proxy. The data proxy will need to make an Ident call
      back to get the scraperID. Since the data proxy may be on another machine
      and the peer address it sees will have been subject to NAT or masquerading,
      send the UML name and the socket port number in the request.
      */

      if (is_null($this->m_socket))
      {
            $this->m_socket    = socket_create (AF_INET, SOCK_STREAM, SOL_TCP) ;
            socket_connect     ($this->m_socket, $this->m_host, $this->m_port) ;
            socket_getsockname ($this->m_socket, $addr, $port) ;
            $getmsg = sprintf  ("GET /?uml=%s&port=%s HTTP/1.1\n\n", trim(`/bin/hostname`), $port) ;
            socket_send        ($this->m_socket, $getmsg, strlen($getmsg), MSG_EOR) ;
            socket_recv        ($this->m_socket, $buffer, 0xffff, 0) ;
            $result = json_decode ($buffer) ;
            if (! $result[0])
               throw new Exception ($result[1]) ;
      }
   }

   function request ($req)
   {
      $this->connect () ;
      $reqmsg  = json_encode ($req) . "\n" ;
      socket_send ($this->m_socket, $reqmsg, strlen($reqmsg), MSG_EOR) ;

      $text = '' ;
      while (true)
      {
            socket_recv ($this->m_socket, $buffer, 0xffff, 0) ;
            if (strlen($buffer) == 0)
               break ;
            $text .= $buffer ;
            if ($text[strlen($text)-1] == "\n")
               break ;
      }

      return json_decode ($text) ;
   }

#function fetch (self, unique_keys_dict) :
#
#        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
#            return [ False, 'unique_keys must a non-empty dictionary' ]
#
#        uunique_keys_dict = mangleflattendict(unique_keys_dict)
#        return $this->request (('fetch', uunique_keys_dict))
#
#function retrieve (self, unique_keys_dict) :
#
#        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
#            return [ False, 'unique_keys must a non-empty dictionary' ]
#
#        uunique_keys_dict = mangleflattendict(unique_keys_dict)
#        return $this->request (('retrieve', uunique_keys_dict))
#    
   function save ($unique_keys, $scraper_data, $date = null, $latlng = null)
   {
#        if type(unique_keys) not in [ types.NoneType, types.ListType, types.TupleType ] :
#            return [ False, 'unique_keys must be None, or a list or tuple' ]
# 
#        if date   is not None :
#            if type(date) not in [ datetime.datetime, datetime.date ] :
#                return [ False, 'date should be a python.datetime (not %s)' % type(date) ]
#
#        if latlng is not None :
#            if type(latlng) not in [ types.ListType, types.TupleType ] or len(latlng) != 2 :
#                return [ False, 'latlng must be a (float,float) list or tuple' ]
#            if type(latlng[0]) not in [ types.IntType, types.LongType, types.FloatType ] :
#                return [ False, 'latlng must be a (float,float) list or tuple' ]
#            if type(latlng[1]) not in [ types.IntType, types.LongType, types.FloatType ] :
#                return [ False, 'latlng must be a (float,float) list or tuple' ]
#
#        if date   is not None :
#            date   = str(date)
#        if latlng is not None :
#            latlng = '%010.6f,%010.6f' % tuple(latlng)
#
      # flatten everything into strings here rather than in the dataproxy/datalib where 
      $js_data      = $this->mangleflattendict($scraper_data) ;

      # unique_keys need to be mangled too so that they match
      $uunique_keys = $this->mangleflattenkeys($unique_keys ) ;

      return $this->request (array('save', $uunique_keys, $js_data, $date, $latlng)) ;
   }

#function postcodeToLatLng (self, postcode) :
#
#        return $this->request (('postcodetolatlng', postcode))
#
#function close (self) :
#
#        $this->m_socket.send ('.\n')
#        $this->m_socket.close()
#        $this->m_socket = None
#

   static function create ($host = null, $port = null)
   {
      if (is_null(self::$m_ds))
         self::$m_ds = new DataStoreClass ($host, $port) ;
      return   self::$m_ds ;
   }
}

function sw_data_save ($unique_keys, $data, $date = null, $latlng = null)
{
   $ds      = DataStoreClass::create () ;

   $result  = $ds->save ($unique_keys, $data, $date = null, $latlng = null) ;
   if (! $result[0])
      throw new Exception ($result[1]) ;

   sw_dumpMessage (array('message_type' => 'data', 'content' => $data)) ;
}

?>
