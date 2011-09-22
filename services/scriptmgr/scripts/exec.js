#!/usr/local/bin/node

var opts = require('opts');
var options = [
  {  long        : 'script', value : true },
  {  long        : 'ds', value : true  },
  {  long        : 'gid', value : true  },
  {  long        : 'uid', value : true  },
  {  long        : 'scrapername', value : true  },
  {  long        : 'attachables', value : true  },
  {  long        : 'qs', value : true  },
  {  long        : 'runid', value : true  },
  {  long        : 'path', value : true  }
];
opts.parse(options, true);

var sw = require('scraperwiki');
var parts = opts.get('ds').split(':');
sw.sqlite.init(parts[0], parts[1], opts.get("scrapername") || "", opts.get("runid") || "");



process.on('SIGXCPU', function () {
	throw 'ScraperWiki CPU time exceeded';
});


process.on('uncaughtException', function (err) {
	sw.dumpMessage( err );
});

try {
	// Load and run the script provided to us
	require( opts.get('script') );
} catch( err ) {
	console.log( err );

	/*
		Need to better handle the stacktrace
	    etb = scraperwiki.stacktrace.getExceptionTraceback(code)  
	    assert etb.get('message_type') == 'exception'
	    scraperwiki.dumpMessage(etb)
	*/
}
