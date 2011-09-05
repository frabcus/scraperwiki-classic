var EventEmitter = process.EventEmitter;


exports.DataProxyClient =  DataProxyClient = function() {
	this.host = "";
	this.port  = 0;
	this.scrapername = "";	
}

DataProxyClient.prototype.__proto__ = EventEmitter.prototype;

DataProxyClient.prototype.init = function(host, port,scrapername) {
	this.host = host;
	this.port = port;
	this.scrapername = scrapername;
}

DataProxyClient.prototype.toString = function() {
	return "DataProxy (" + this.host + ":" + this.port + ")";
}