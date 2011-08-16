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
var qs   = require('querystring');

var exec = require('./executor');

_routemap = {
	'/Execute'   : handleRun,
	'/kill'  : handleKill,
	'/status': handleStatus,
	'/Ident' : handleIdent,
	'/Notify': handleNotify,
	'/'      : handleUrlError,
};

// default settings options
_config = { 
	devmode: true, 
	port: 9001, 
	vm_count: 50, 
	extra_path: '../../scraperlibs',
	dataproxy: '127.0.0.1:9003',
	httpproxy: '127.0.0.1:9005',
};

/******************************************************************************
* Initialises the http server used for accepting (and then processing) requests
* from a remote dispatcher service.  In general once a request has been 
* accepted it is long running until the connection is closed, or local script
* execution is stopped.
******************************************************************************/

exec.set_config( _config );


http.createServer(function (req, res) {
	var handler = _routemap[url.parse(req.url).pathname] || _routemap['/']
	handler(req,res)
	
}).listen(_config.port, "127.0.0.1");

console.log('+ Server started listening on port ' + _config.port );
	

/******************************************************************************
* Handles a run request when a client POSTs code to be executed along with a 
* run id, a scraper id and the scraper name
*
******************************************************************************/
function handleRun(req,res) {
	console.log( '+ Handling /run request' );
	exec.run_script( req, res);
	console.log( '+ Run request completed' );	
}

/******************************************************************************
* When provided with a Run ID (run_id) then it will attempt to kill the script
* by sending the request on to the executor which will either lxc-kill or 
* sigkill the relevant script.
******************************************************************************/
function handleKill(req,res) {
	console.log( '+ Handling kill request' );

	var url_parts = url.parse(req.url, true);
	var query = url_parts.query;
	
	if ( ! query.run_id ) {
		write_error( res, "Missing parameter" );
		return;
	}

	var result = exec.kill_script( query.run_id );
	if ( ! result ) {
		write_error( res, "Failed to kill script, may no longer be running" );
		return;
	}
	res.end();	
}

/******************************************************************************
* Returns the status of the service, which is essentially just a list of run
* ids and names.  This is the same regardless of execution method.
******************************************************************************/
function handleStatus(req,res) {
	
	exec.get_status(res);
	res.end('');	
}

/******************************************************************************
* Handle ident callback from http proxy
*
******************************************************************************/
function handleIdent(req,res) {
	
 	var urlObj = url.parse(req.url, true);	
	console.log( "**************************************** IDENT" );
	console.log( urlObj );
	console.log( "**********************************************" );	
	
	// call exec.get_details(details) and return it
/* for line in string.split (ident, '\n'):
            if line == '' :
                continue
            key, value = string.split (line, '=')
            if key == 'runid' :
                runID     = value
                continue
            if key == 'scraperid' :
                scraperID = value
                continue
            if key == 'allow'  :
                self.m_allowed.append (value)
                continue
            if key == 'block'  :
                self.m_blocked.append (value)
                continue
            if key == 'option' :
                name, opt = string.split (value, ':')
                if name == 'webcache' : cache = int(opt)
*/
		
	res.end('/ident');	
}

/******************************************************************************
* Handle notify callback from http proxy
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

/******************************************************************************
* Write the error message in our standard (ish) json format
******************************************************************************/
function write_error(res, msg, headers) {
	r = {"error": msg, "headers": headers || '' , "lengths":  -1 };
	res.end( JSON.stringify(r) );
}