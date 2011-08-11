/******************************************************************************
* scriptmgr.js
*
* Provides script management services to a dispatching service to allow for the 
* execution of code from webapp users within an LXC (when not in dev mode). The
* behaviour of the service is the same as the original UML controller.py and 
* accepts url requests in the same format with the same parameters.
*
* Acceptable urls are listed below, but see the relevant functions for the
* expected parameters:
*
*	/run    - Run the provided code within an LXC container and return all of 
*			  the output on the same connection (as our response).
*	/kill   - Kill the specified scraper (by stopping its container)
*	/status - Return a list of all of the current containers and the 
*			  information about what is running
* 	/ident  - Accept an ident request from the httpproxy so that it can 
*			  determine the source of the request
* 	/notify - Called by the httpproxy to let us know what URL the scraper
*			  has requested (so we can send it back and add to the sources
*			  tab in the editor)
* 
******************************************************************************/
var http = require('http');
var url  = require('url');
var _    = require('underscore')._;

var exec = require('./executor');

_routemap = {
	'/run'   : handleRun,
	'/kill'  : handleKill,
	'/status': handleStatus,
	'/ident' : handleIdent,
	'/notify': handleNotify,
	'/'      : handleUrlError,
};

// default settings options
_config = { devmode: true, port: 8001 }

/******************************************************************************
* Initialises the http server used for accepting (and then processing) requests
* from a remote dispatcher service.  In general once a request has been 
* accepted it is long running until the connection is closed, or local script
* execution is stopped.
******************************************************************************/
// Check parameters

exec.set_mode( _config.devmode );


http.createServer(function (req, res) {
	
	var handler = _routemap[url.parse(req.url).pathname] || _routemap['/']
	handler(req,res)
	
}).listen(8001, "127.0.0.1");

console.log('+ Server started listening on port ' + _config.port );
	

/******************************************************************************
*
*
******************************************************************************/
function handleRun(req,res) {
	console.log( '+ Handling /run request' );
	exec.run_script( req, res);
}

/******************************************************************************
*
*
******************************************************************************/
function handleKill(req,res) {
	console.log( '+ Handling /kill request' );
		
    // call exec.kill_script(run_id) and depending on result 
	// we should decide what to do

	res.end('/kill');	
}

/******************************************************************************
*
*
******************************************************************************/
function handleStatus(req,res) {
	
	// call exec.get_status() and return it
	
	res.end('/status');	
}

/******************************************************************************
*
*
******************************************************************************/
function handleIdent(req,res) {
	
	// call exec.get_details(details) and return it
		
	res.end('/ident');	
}

/******************************************************************************
*
*
******************************************************************************/
function handleNotify(req,res) {
	res.end('/notify');	
}
	

/******************************************************************************
* Unknown URL called.  Will return 404 to denote that it wasn't found rather 
* than it not being valid somehow.
******************************************************************************/
function handleUrlError(req,res) { 
	res.writeHead(404, {'Content-Type': 'text/html'}); 
	res.end('URL not found'); 
}	
