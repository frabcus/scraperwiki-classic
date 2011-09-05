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
	this.connection = null;
	this.ensureConnected();
}

DataProxyClient.prototype.ensureConnected = function() {
	if ( this.connection != null ) return;
	
	console.log('Creating a new connection');
	this.connection = net.createConnection(this.port, this.host);
	this.connection.setEncoding( 'utf8');
	
	var me = this;
	this.connection.on('connect', function(){
        var data = {"uml": me.connection.address().address , "port": me.connection.address().port}
        data["vscrapername"] = me.scrapername;
        data["vrunid"] = me.runid
        data["attachables"] = me.attachables.join(" ")

		me.connection.once('data', function (data) {
	  		console.log(data);
		});

		// naughty semi-http request.... sigh
		var msg = "GET /?" + qs.stringify(data) + "HTTP/1.1\r\n\r\n";
		me.connection.write( msg, function(){
			console.log('Wrote data');
			console.log('Now waiting to readdata');
		});
/*        
#        line = receiveoneline(m_socket)  # comes back with True, "Ok"
#        res = json.loads(line)
#        assert res.get("status") == "good", res*/
		
	});	
}

DataProxyClient.prototype.save = function(indices, data, verbose) {
	if ( verbose == null ) verbose = 2;
	
	return "DataProxy (" + this.host + ":" + this.port + " - " +  this.scrapername +")";
}

DataProxyClient.prototype.toString = function() {
	return "DataProxy (" + this.host + ":" + this.port + " - " +  this.scrapername +")";
}
