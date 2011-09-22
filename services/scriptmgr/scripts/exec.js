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

var scriptfile = opts.get('script');
try {
	// Load and run the script provided to us
	require( scriptfile );
} catch( err ) {
	// parse err.stack for nice clean presentation. We still need line 
	// numbers adding here.
	var stack = [];
	var lines = err.stack.split('\n');

	// Get line number from lines[1] which looks a bit like
	// at Object.<anonymous> (/private/tmp/script.js:3:9)
	var linenum = lines[1].match(/\d+/)[0];

	stack.push( {"duplicates": 0, "linetext": lines[0].trim(), "file": "<string>", "linenumber": parseInt(linenum)} )
	
	for ( var p = 1; p < lines.length; p++ ) {
		var m = lines[p].trim();
		if ( m.length > 0 )
			stack.push( { "file": m, "linetext" : m, "linenumber": parseInt(linenum)}  );
	}
	
	var result = { "message_type": "exception", 
"linenumber": parseInt(linenum),
				   "stackdump": stack };	
	sw.dumpMessage( JSON.stringify(result) );    
}
