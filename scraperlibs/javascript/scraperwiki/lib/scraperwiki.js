
exports.version = '1.0.0';


exports.sqlite = new DataProxyClient();



function DataProxyClient() {
}

DataProxyClient.prototype.toString = function() {
	return "DataProxy";
}