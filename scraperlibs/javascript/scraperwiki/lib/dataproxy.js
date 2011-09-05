var EventEmitter = process.EventEmitter;
var net = require('net');

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
	
	this.ensureConnected();
}

DataProxyClient.prototype.ensureConnected = function() {
	if ( this.connection != null ) return;
	console.log('Creating a new connection');
	this.connection = net.createConnection(self.port, self.host);
	this.connection.on('connect', function(){
        var data = {"uml":socket.gethostname(), "port":m_socket.getsockname()[1]}
        data["vscrapername"] = this.scrapername;
        data["vrunid"] = this.runid
        data["attachables"] = this.attachables.join(" ")
		console.log('Is going to be ...');
		console.log( data );
/*        m_socket.sendall('GET /?%s HTTP/1.1\n\n' % urllib.urlencode(data))
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
