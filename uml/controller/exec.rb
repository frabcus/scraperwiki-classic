#!/usr/bin/ruby

# moved to the top because syntax errors in the scraperlibs otherwise are difficult to detect
#
$stdout = IO.new(1)
$stderr = IO.new(2)

require 'json'

class ConsoleStream

    def initialize(fd)
        @fd   = fd
        @text = ''
    end

    def write(text)
        @text = @text + text
        if @text.length > 0 && @text[-1] == "\n"[0]
            flush
        end
    end

    def flush
      if @text != ''
          message = { 'message_type' => 'console', 'content' => @text }
          @fd.write(JSON.generate(message) + "\n")
          @text = ''
      end
    end

    def close
        @fd.close()
    end

end


USAGE       = ' [--cache=N] [--trace=mode] [--script=name] [--path=path] [--scraperid=id] [--runid=id] [-http=proxy] [--https=proxy] [--ftp=proxy] [--ds=server:port]'
cache       = nil
trace       = nil
script      = nil
path        = nil
scraperID   = nil
runID       = nil
httpProxy   = nil
httpsProxy  = nil
ftpProxy    = nil
datastore   = nil
uid         = nil
gid         = nil

ARGV.each do |a|

    if a.slice(0.. 7) == '--cache='
        cache      = a.slice(8 ..-1).to_i
        next
    end

    if a.slice(0.. 7) == '--trace='
        trace      = a.slice(8 ..-1)
        next
    end

    if a.slice(0.. 8) == '--script='
        script     = a.slice(9 ..-1)
        next
    end

    if a.slice(0..11) == '--scraperid='
        scraperID  = a.slice(12..-1)
        next
    end

    if a.slice(0.. 7) == '--runid='
        runID      = a.slice(8 ..-1)
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
        datastore  = a.slice(5 ..-1)
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

#print   "cache     =", cache,      "\n"
#print   "trace     =", trace,      "\n"
#print   "script    =", script,     "\n"
#print   "path      =", path,       "\n"
#print   "scraperID =", scraperID,  "\n"
#print   "runID     =", runID,      "\n"
#print   "httpProxy =", httpProxy,  "\n"
#print   "httpsProxy=", httpsProxy, "\n"
#print   "ftpProxy  =", ftpProxy,   "\n"
#print   "datastore =", datastore,  "\n"
#print   "uid       =", uid,        "\n"
#print   "gid       =", gid,        "\n"

if gid
    Process::Sys.setregid(gid, gid)
end
if uid
    Process::Sys.setreuid(uid, uid)
end

if path
    path.split(':').each { |p| $LOAD_PATH << p ; }
end

require	'scraperwiki'

$logfd  = IO.new(3)

if cache
    ScraperWiki.allowCache(cache) ;
end

##  Pass the configuration to the datastore. At this stage no connection
##  is made; a connection will be made on demand if the scraper tries
##  to save anything.
##
require 'scraperwiki/datastore'
host, port = datastore.split(':')
SW_DataStore.create(host, port)

#
##  Set up a CPU time limit handler which simply throws a python
##  exception.
##
#def sigXCPU (signum, frame) :
#    raise Exception ("CPUTimeExceeded")
#
#signal.signal (signal.SIGXCPU, sigXCPU)

eval File.new(script, 'r').read()
