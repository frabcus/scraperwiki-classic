#!/usr/bin/ruby

$stdout.sync = true

require 'rubygems'   # for nokigiri to work on all machines, and for JSON/Iconv on OSX
require 'json'
require 'iconv'
require 'optparse'
require	'scraperwiki'
require 'scraperwiki/datastore'
require 'scraperwiki/stacktrace'

$logfd  = IO.new(3)

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

$stdout = ConsoleStream.new($logfd)
$stderr = ConsoleStream.new($logfd)

Signal.trap("XCPU") do
    raise Exception, "ScraperWiki CPU time exceeded"
end

options = {}
OptionParser.new do|opts|
   opts.on( '--script=[SCRIPT]') do|script|
     options[:script] = script
   end
   opts.on( '--ds=[DS]') do|ds|
     options[:ds] = ds
   end
   opts.on( '--gid=[GID]') do|gid|
     Process::Sys.setregid(gid.to_i, gid.to_i)
   end
   opts.on( '--uid=[UID]') do|uid|
     Process::Sys.setreuid(uid.to_i, uid.to_i)
   end
end.parse(ARGV)

host, port = options[:ds].split(':')
SW_DataStore.create(host, port)

code = File.new(options[:script], 'r').read()
begin
    eval code
rescue Exception => e
    est = getExceptionTraceback(e, code)
    # for debugging:
    # File.open("/tmp/fairuby", 'a') {|f| f.write(JSON.generate(est)) }
    $logfd.write(JSON.generate(est) + "\n")
end

$stdout.flush
$stderr.flush
