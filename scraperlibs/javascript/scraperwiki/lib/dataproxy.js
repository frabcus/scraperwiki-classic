var EventEmitter = process.EventEmitter;
var net = require('net');
var qs = require('querystring');

exports.DataProxyClient =  DataProxyClient = function() {
	this.host = "";
	this.port  = 0;
	this.scrapername = "";	
	this.connection = null;
}

DataProxyClient.prototype.__proto__ = EventEmitter.prototype;

DataProxyClient.prototype.init = function(host, port,scrapername,runid) {
	this.host = host;
	this.port = port;
	this.scrapername = scrapername;
	this.runid = runid;
	this.attachables = [];
	this.connected = false;
}

DataProxyClient.prototype.ensureConnected = function( callback ) {
	if ( this.connected ) { 
		callback(this.connected);
		return;
	}
	
	console.log('Creating a new connection');
	this.connection = net.createConnection(this.port, this.host);
	this.connection.setEncoding( 'utf8');
	
	var me = this;
	this.connection.once('data', function (data) {
		var str = JSON.parse( data );
		me.connected = str.status && str.status == 'good';
		callback(me.connected);
		return;
	});
	
	this.connection.on('connect', function(){
        var data = {"uml": me.connection.address().address , "port": me.connection.address().port}
        data["vscrapername"] = me.scrapername;
        data["vrunid"] = me.runid
        data["attachables"] = me.attachables.join(" ")

		// naughty semi-http request.... sigh
		var msg = "GET /?" + qs.stringify(data) + "HTTP/1.1\r\n\r\n";
		me.connection.write( msg, function(){
			console.log('Wrote data');
		});
	});	
}

DataProxyClient.prototype.close = function() {
	if ( this.connected ) {
		this.connection.end();
		this.connected = false;
	}
}
	
DataProxyClient.prototype.save = function(indices, data, verbose, callback) {
	if ( verbose == null ) verbose = 2;
	var self = this;
	this.ensureConnected(function(ok){
		if ( ok ) {
			internal_save(indices,data,verbose);
			callback( "DataProxy (" + self.host + ":" + self.port + " - " +  self.scrapername +")" );
		}
	});
}

function internal_save(callback) {
	console.log( 'internal save ')
};


DataProxyClient.prototype.toString = function() {
	return "DataProxy (" + this.host + ":" + this.port + " - " +  this.scrapername +")";
}
