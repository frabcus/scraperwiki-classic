#!/usr/local/bin/node 

var opts = require('opts');
var options = [
  {  long        : 'script', value : true },
  {  long        : 'ds', value : true  },
  {  long        : 'gid', value : true  },
  {  long        : 'uid', value : true  },
  {  long        : 'scrapername', value : true  },
  {  long        : 'runid', value : true  },
  {  long        : 'path', value : true  }
];
opts.parse(options);

/*
if options.gid:
    os.setregid(int(options.gid), int(options.gid))
if options.uid:
    os.setreuid(int(options.uid), int(options.uid))
if options.path:
    sys.path.append( options.path )
*/


/*host, port = string.split(options.ds, ':')
scraperwiki.datastore.create(host, port, options.scrapername or "", options.runid)

scraperwiki.logfd = sys.stderr

# in the future can divert to webproxy
#scraperwiki.utils.urllibSetup(http_proxy='http://127.0.0.1:9002')
*/

process.on('SIGXCPU', function () {
	throw 'ScraperWiki CPU time exceeded';
});

try {
	var script = require(opts.get('script'));
	script.main();
} catch( err ) {
	console.log( err );
}
/*
code = open(options.script).read()
try:
    import imp
    mod = imp.new_module('scraper')
    exec code.rstrip() + "\n" in mod.__dict__

except Exception, e:
    etb = scraperwiki.stacktrace.getExceptionTraceback(code)  
    assert etb.get('message_type') == 'exception'
    scraperwiki.dumpMessage(etb)
*/