var request = require('request');
var dp = require('./dataproxy');

exports.version = '1.0.0';

exports.sqlite = new DataProxyClient();

exports.dumpMessage = function(msg) {
	console.log( "JSONRECORD(" + msg.length.toString() + "):" + msg + "\n" );
}

exports.scrape = function( url, callback ) {
	request(url, function (error, response, body) {
	  if (!error && response.statusCode == 200) {
	    callback( body );
	  } else {
		// Parse the stack and throw it with our new throw
		throw(error);
	}
})};
