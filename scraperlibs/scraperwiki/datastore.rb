require 'json'

$M_DS	= nil

class SW_DataStore

    def initialize(host, port)
        @m_socket    = nil
        @m_host      = host
        @m_port      = port
    end

    def mangleflattendict(data)

        rdata = {}
        data.each_pair do |key, value|
            rkey = key.gsub(' ', '_')
            if value == nil
                rvalue  = ''
            elsif  value.eql?(true )
                rvalue  = '1'
            elsif value.eql?(false)
                rvalue  = '0'
            else
                rvalue  = value.to_s
            end
            rdata[rkey] = rvalue ;
        end
        return rdata
    end

    def mangleflattenkeys(keys)
        rkeys = []
        keys.each do |key|
            rkeys.push(key.gsub(' ', '_'))
        end
        return rkeys
    end

    def connect()
        # Connect to the data proxy. The data proxy will need to make an Ident call
        # back to get the scraperID. Since the data proxy may be on another machine
        # and the peer address it sees will have been subject to NAT or masquerading,
        # send the UML name and the socket port number in the request.
        if @m_socket == nil
            @m_socket = TCPSocket.open(@m_host, @m_port)
            proto, port, name, ip = @m_socket.addr()
            getmsg = "GET /?uml=%s&port=%s HTTP/1.1\n\n" % [Socket.gethostname(), port]
            @m_socket.send(getmsg, 0)
            buffer = @m_socket.recv(1024)
            result = JSON.parse(buffer)
            if ! result[0]
                raise result[1]
            end
        end
    end

    def request (req)
        connect()
        reqmsg  = JSON.generate(req)
        @m_socket.send(reqmsg + "\n", 0)
        text = ''
        while true
            buffer = @m_socket.recv(1024)
            if buffer.length == 0
                break
            end
            text += buffer
            if text[-1] == "\n"[0]
                break
            end
        end
        return JSON.parse(text)
    end

    def save(unique_keys, scraper_data, date = nil, latlng = nil)
        if unique_keys != nil && !unique_keys.kind_of?(Array)
            return [false, 'unique_keys must be nil or an array']
        end

# the following code is for ensuring that the date and latlng values have the 
# correct type and converting them into appropriate formated strings
# (not coded in Ruby as I don't know how, but done in PHP and Python)

##     if date   is not None :
##        if type(date) not in [ datetime.datetime, datetime.date ] :
##            return [ False, 'date should be a python.datetime (not %s)' % type(date) ]
#
#      if (!is_null($latlng))
#      {
#         if (!is_array($latlng) || count($latlng) != 2)
#            return array (false, 'latlng must be a (float,float) list or tuple') ;
#         if (!is_numeric($latlng[0]) || !is_numeric($latlng[1]) )
#            return array (false, 'latlng must be a (float,float) list or tuple') ;
#      }
#
##     if date   is not None :
##         date   = str(date)
#
#      if (!is_null($latlng))
#         $latlng = sprintf ('%010.6f,%010.6f', $latlng[0], $latlan[1]) ;
#
        # flatten everything into strings here rather than in the dataproxy/datalib
        # unique_keys need to be mangled too so that they match
        #
        js_data      = mangleflattendict(scraper_data)
        uunique_keys = mangleflattenkeys(unique_keys )
        return request(['save', uunique_keys, js_data, date, latlng])
    end

    def SW_DataStore.create(host = nil, port = nil)
        if ! $M_DS
            $M_DS = SW_DataStore.new(host, port)
        end
        return $M_DS
    end

end


#
#
##function fetch (self, unique_keys_dict) :
##
##        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
##            return [ False, 'unique_keys must a non-empty dictionary' ]
##
##        uunique_keys_dict = mangleflattendict(unique_keys_dict)
##        return $this->request (('fetch', uunique_keys_dict))
##
##function retrieve (self, unique_keys_dict) :
##
##        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
##            return [ False, 'unique_keys must a non-empty dictionary' ]
##
##        uunique_keys_dict = mangleflattendict(unique_keys_dict)
##        return $this->request (('retrieve', uunique_keys_dict))
##    
#
#   function postcodeToLatLng ($postcode)
#   {
#      return $this->request (array ('postcodetolatlng', $postcode)) ;
#   }
#
#   function close ()
#   {
#      socket_send  ($this->m_socket, ".\n", 2, MSG_EOR) ;
#      socket_close ($this->m_socket) ;
#      $this->m_socket = undef ;
#   }
#
