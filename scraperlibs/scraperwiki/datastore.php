<?php

class SW_DataStoreClass
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
         $rkeys[] = str_replace (' ', '_', $key) ;
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
      if (!is_null($unique_keys) && !is_array($unique_keys))
         return array (false, 'unique_keys must be null, or an array') ;
#
#     if date   is not None :
#        if type(date) not in [ datetime.datetime, datetime.date ] :
#            return [ False, 'date should be a python.datetime (not %s)' % type(date) ]

      if (!is_null($latlng))
      {
         if (!is_array($latlng) || count($latlng) != 2)
            return array (false, 'latlng must be a (float,float) array') ;
         if (!is_numeric($latlng[0]) || !is_numeric($latlng[1]) )
            return array (false, 'latlng must be a (float,float) array') ;
      }

#     if date   is not None :
#         date   = str(date)

      if (!is_null($latlng))
         $latlng = sprintf ('%010.6f,%010.6f', $latlng[0], $latlng[1]) ;

      # flatten everything into strings here rather than in the dataproxy/datalib
      #
      $js_data      = $this->mangleflattendict($scraper_data) ;

      # unique_keys need to be mangled too so that they match
      #
      $uunique_keys = $this->mangleflattenkeys($unique_keys ) ;

      return $this->request (array('save', $uunique_keys, $js_data, $date, $latlng)) ;
   }

   function postcodeToLatLng ($postcode)
   {
      return $this->request (array ('postcodetolatlng', $postcode)) ;
   }

   function close ()
   {
      socket_send  ($this->m_socket, ".\n", 2, MSG_EOR) ;
      socket_close ($this->m_socket) ;
      $this->m_socket = undef ;
   }

   static function create ($host = null, $port = null)
   {
      if (is_null(self::$m_ds))
         self::$m_ds = new SW_DataStoreClass ($host, $port) ;
      return   self::$m_ds ;
   }
}

?>
