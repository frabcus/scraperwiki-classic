require 'json'
require 'singleton'
require 'thread'

# the python version of this makes use of a global static copy of the class 
# so the connection is made only once to the dataproxy
# I think the Singleton module implements this magically

class SW_DataStore
    
    @@lock = Mutex.new
    
    include Singleton

    attr_accessor :m_port, :m_host

    def initialize
      @m_socket = nil
      @m_host = nil
      @m_port = nil
    end


    def ensure_connected
        # Connect to the data proxy. The data proxy will need to make an Ident call
        # back to get the scraperID. Since the data proxy may be on another machine
        # and the peer address it sees will have been subject to NAT or masquerading,
        # send the UML name and the socket port number in the request.
        if @m_socket == nil
            @m_socket = TCPSocket.open(@m_host, @m_port)
            proto, port, name, ip = @m_socket.addr()
            getmsg = "GET /?uml=%s&port=%s HTTP/1.1\n\n" % [Socket.gethostname(), port]
            @m_socket.send(getmsg, 0)
            @m_socket.flush()
            buffer = @m_socket.recv(1024)
            result = JSON.parse(buffer)
            if result["status"] != "good"
                raise result["status"]
            end
        end
    end

    def request (req)
        text = ''
        @@lock.synchronize {
          ensure_connected
          reqmsg  = JSON.generate(req) + "\n"

          bytes_sent = 0
          while bytes_sent < reqmsg.length
            bytes_sent += @m_socket.send(reqmsg.slice(bytes_sent, reqmsg.length), 0)
          end
          @m_socket.flush()

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
        }
        return JSON.parse(text)
    end

    def SW_DataStore.create(host = nil, port = nil)
        instance = SW_DataStore.instance
        # so, it might be intended that the host and port are
        # set once, never to be changed, but this is ruby so
        # there's no way to guarantee that.
        if host && port && instance.m_port.nil? && instance.m_host.nil?
          instance.m_host = host
          instance.m_port = port
        elsif host && port
          raise "Can't change host and port once connection made"
        elsif !(instance.m_port) || !(instance.m_host)
          raise "Can't return a datastore without port/host information"
        end
        instance
    end
end
