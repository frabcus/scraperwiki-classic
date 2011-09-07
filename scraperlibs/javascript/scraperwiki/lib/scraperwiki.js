var dp = require('./dataproxy')

exports.version = '1.0.0';

exports.sqlite = new DataProxyClient();


exports.scrape = function( url, callback ) {
	
	callback('');
};
