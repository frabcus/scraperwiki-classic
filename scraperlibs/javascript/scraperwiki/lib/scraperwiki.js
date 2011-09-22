//var request = require('request');
var dp = require('./dataproxy');

exports.version = '1.0.0';

exports.sqlite = new DataProxyClient();

exports.dumpMessage = function(msg) {
	sys.stderr.write( "JSONRECORD(" + msg.length.toString() + "):" + msg + "\n" );
}



exports.scrape = function( url, callback ) {
/*  request({uri: url}, function (error, response, body) {
      callback(body);
  });*/
};
