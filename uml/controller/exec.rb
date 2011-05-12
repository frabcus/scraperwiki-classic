#!/usr/bin/ruby

require 'json'
require 'iconv'

class ConsoleStream

    def initialize(fd)
        @fd   = fd
        @text = ''
    end

    # Do our best to turn anything into unicode, for display on console
    # (for datastore, we give errors if it isn't already UTF-8)
    def saveunicode(text)
        begin
            text = Iconv.conv('utf-8', 'utf-8', text)
        rescue Iconv::IllegalSequence
            begin
                text = Iconv.conv('utf-8', 'iso-8859-1', text)
            rescue Iconv::IllegalSequence
                text = Iconv.conv('utf-8//IGNORE', 'utf-8', text)
            end
        end
        return text
    end

    def write(text)
        @text = @text + saveunicode(text)
        if @text.length > 0 && @text[-1] == "\n"[0]
            flush
        end
    end

    def <<(text)
       write text
    end

    def flush
      if @text != ''
          message = { 'message_type' => 'console', 'content' => @text }
          @fd.write(JSON.generate(message) + "\n")
          @fd.flush
          @text = ''
      end
    end

    def close
        @fd.close()
    end

end


USAGE       = ' [--script=name] [--path=path] [-http=proxy] [--https=proxy] [--ftp=proxy] [--ds=server:port]'
script      = nil
path        = nil
httpProxy   = nil
httpsProxy  = nil
ftpProxy    = nil
ds   = nil
uid         = nil
gid         = nil

ARGV.each do |a|

    if a.slice(0.. 8) == '--script='
        script     = a.slice(9 ..-1)
        next
    end

    if a.slice(0.. 6) == '--path='
        path       = a.slice(7 ..-1)
        next
    end

    if a.slice(0.. 6) == '--http='
        httpProxy  = a.slice(7 ..-1)
        next
    end

    if a.slice(0.. 7) == '--https='
        httpsProxy = a.slice(8 ..-1)
        next
    end

    if a.slice(0.. 5) == '--ftp='
        ftpProxy   = a.slice(6 ..-1)
        next
    end

    if a.slice(0.. 4) == '--ds='
        ds  = a.slice(5 ..-1)
        next
    end

    if a.slice(0.. 5) == '--uid='
        uid        = a.slice(6 ..-1).to_i
        next
    end

    if a.slice(0.. 5) == '--gid='
        gid        = a.slice(6 ..-1).to_i
        next
    end

    print "usage: ", "exec.rb ", USAGE
    Process.exit(1)
end

if gid    # nogroup
    Process::Sys.setregid(gid, gid)
end
if uid    # nobody
    Process::Sys.setreuid(uid, uid)
end

if path
    path.split(':').each { |p| $LOAD_PATH << p ; }
end

require	'scraperwiki'

$logfd  = IO.new(3)
$stdout = ConsoleStream.new($logfd)
$stderr = ConsoleStream.new($logfd)


##  Pass the configuration to the datastore. At this stage no connection
##  is made; a connection will be made on demand if the scraper tries
##  to save anything.
##
require 'scraperwiki/datastore'
host, port = ds.split(':')
SW_DataStore.create(host, port)

require 'scraperwiki/stacktrace'

#  Set up a CPU time limit handler which simply throws a Ruby
#  exception.
Signal.trap("XCPU") do
    raise Exception, "ScraperWiki CPU time exceeded"
end

ARGV.clear # Clear command line args so that we can use Test::Unit

code = File.new(script, 'r').read()
begin
    require 'rubygems'   # for nokigiri to work
    eval code
rescue Exception => e
    est = getExceptionTraceback(e, code)
    # for debugging:
    # File.open("/tmp/fairuby", 'a') {|f| f.write(JSON.generate(est)) }
    $logfd.write(JSON.generate(est) + "\n")
end


# force ConsoleStream to output last line, even if no \n
$stdout.flush
$stderr.flush
