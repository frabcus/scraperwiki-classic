/******************************************************************************
* switchboard.js
*
* A simple switchboard that accepts input from N writers and streams it all to
* M registered readers, all based on a key - the run_id. When a client wants 
* to run a script it can be told where to call (as a writer) and have the data
* written to any client who has registered as a reader with the run_id. If 
* there are no registered readers then data is likely to be dropped onto the 
* floor, after the initial buffer has been accepted and filled.
* 
******************************************************************************/
var path = require('path');
var http = require('http');
var url  = require('url');
var _    = require('underscore')._;
var opts = require('opts');

var logging = require( path.join(__dirname,'logging'))


// Handle uncaught exceptions and make sure they get logged
process.on('uncaughtException', function (err) {
  util.log.fatal('Caught exception: ' + err);
  if ( settings.devmode ) console.log( err.stack );
});


var options = [
  { short       : 'c', 
	long        : 'config',
    description : 'Specify the configuration file to use',
	value : true 
  }
];
opts.parse(options, true);

var config_path = opts.get('config') || './appsettings.switchboard.js';
var settings = require(config_path).settings;
logging.setup( settings.logfile, settings.loglevel );







