/******************************************************************************
* executor.js
*
* 
* 
******************************************************************************/
var lxc = require('./lxc')
var mu  = require('mu')
var qs  = require('querystring');
var fs  = require('fs');
var spawn = require('child_process').spawn;

// Should we lxc, or are we running on a dev machine?
var use_lxc = true;

/******************************************************************************
* 
* 
******************************************************************************/
exports.set_mode = function( is_dev_mode ) {
	use_lxc = !is_dev_mode;
}


/******************************************************************************
* 
* 
******************************************************************************/
exports.kill_script = function( run_id ) {
	
}



/******************************************************************************
* 
* 
******************************************************************************/
exports.get_status = function() {
	
}

/******************************************************************************
* 
* 
******************************************************************************/
exports.get_details = function(details) {
	
}


/******************************************************************************
* Works out from the incoming request what it is that needs executing, if 
* we can find it from the post data.
******************************************************************************/
exports.run_script = function( http_request, http_response ) {
	
	// Handle the request being closed by the client	
	http_request.on("close", function() {
		console.log('- Client killed the connection')
		http_response.end();
	});
	
	len = http_request.headers['content-length'] || -1
	var body = '';
    http_request.on('data', function (data) {
    	body += data;
	});
	
    http_request.on('end', function () {
        var post_data = qs.parse(body);
		if ( body == undefined || body.length == 0 || body.length != len ) {
			r = {"error":"incoming message incomplete", "headers": http_request.headers , "lengths":  len.toString() };
			http_response.end( JSON.stringify(r) );
			return;
		};
		
		execute(http_request, http_response, post_data);
	});
		
};

function execute(http_req, http_res, request_data) {
	http_res.writeHead(200, {'Content-Type': 'text/plain'});
	
	run_id 		 = request_data.run_id;
	scraper_name = request_data.scrapername;
	scraper_guid = request_data.scraperid;
	query 		 = request_data.urlquery;

	if ( ! use_lxc ) {
		// Execute the code locally using the relevant file (exec.whatever)
		var tmpfile = '/tmp/script.py';
		
		// write request_data.code to tmpfile
		fs.writeFile(tmpfile, request_data.code, function(err) {
    		if(err) {
        		sys.puts(err);
    		} else {
				e = spawn('./exec.py', ['--script ',tmpfile,'--ds','127.0.0.1:9005','--scrapername',scraper_name, '--runid', run_id]);
				e.stdout.on('data', function (data) {
					// We need to write this and stderr back to the controller.
  					console.log('stdout: ' + data);
				});
				e.stderr.on('data', function (data) {
  					console.log('stdout: ' + data);
				});				
				e.on('exit', function (code) {
  					console.log('child process exited with code ' + code);
				});
    		}
		}); 		

		
	} else {
		// Use LXC to allocate us an instance so that we can use it....
	}


	http_res.end();
	
	/*
        self.idents.append('scraperid=%s' % scraperguid)
        self.idents.append('runid=%s' % self.m_runID)
        self.idents.append('scrapername=%s' % scrapername)
        for value in request['white']:
            self.idents.append('allow=%s' % value)
        for value in request['black']:
            self.idents.append('block=%s' % value)

        streamprintsin, streamprintsout = socket.socketpair()
        streamjsonsin, streamjsonsout = socket.socketpair()
       */
	
}
