#!/usr/local/bin/node

var fs = require('fs');

var opts = require('opts');
var options = [
  {  long        : 'script', value : true },
  {  long        : 'attachables', value : true  },
];
opts.parse(options, true);

var launch = JSON.parse( fs.readFileSync('launch.json', 'utf-8') );
var datastore = launch['datastore'];
var runid = launch['runid'];
var scrapername = launch['scrapername'];
var querystring = launch['querystring'];

# TODO: Set querystring

var sw = require('scraperwiki');
var parts = datastore.split(':');
sw.sqlite.init(parts[0], parts[1], scrapername, runid);

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
	sw.parseError( err );
	process.exit(1);
}
