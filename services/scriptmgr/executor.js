/******************************************************************************
* executor.js
*
* A running script is indexed by its run_id but looks similar to the following
* for both status and kill calls
* 
*	script = { run_id : request_data.run_id, 
*			 	scraper_name : request_data.scrapername,
*			    scraper_guid : request_data.scraperid,
*			 	query : request_data.urlquery, 
*			 	pid: -1, 
*				vm: '', 
*				language: request_data.language || 'python',
*				ip: ''};
* 
******************************************************************************/
var lxc = require('./lxc')
var util = require('./utils')
var qs  = require('querystring');
var fs  = require('fs');
var spawn = require('child_process').spawn;

var use_lxc = true;
var extra_path;

// A list of all of the currently running scripts
var scripts = [ ];
var scripts_ip = [ ];
var max_runs = 100;

/******************************************************************************
* Called to configure the executor, allowing it to determine whether we are
* using LXC, or whether it is on a local dev machine.
******************************************************************************/
exports.set_config = function( config ) {
	use_lxc = ! config.devmode;

	if ( use_lxc ) {
		console.log('Initialising LXC...')
		lxc.init(config.vm_count);
	}
	
	extra_path = config.extra_path;
	max_runs = config.vm_count;
}


/******************************************************************************
* Attempts to kill the script that is running with the specified run id whether 
* it is an lxc instance (lxc-kill) or a local process (kill by pid)
******************************************************************************/
exports.kill_script = function( run_id ) {
	if ( ! use_lxc ) {
		var s = scripts[run_id];
		if ( s ) {
			pid = s.pid;
			process.kill(pid, 'SIGKILL');
			delete scripts[run_id];
			
  			console.log('Killed process PID: ' + pid);					
			return true;
		};
	}	
	
	return false;
}



/******************************************************************************
* Iterates through the list of scripts that we know is running and outputs 
* them in the old format of runID=&scrapername=
******************************************************************************/
exports.get_status = function(response) {
    for(var runID in scripts) {
		var script = scripts[runID];
		response.write('runID=' + runID + "&scrapername=" + script.scraper_name + "\n");
	}	
	
	console.log("+ Get status returning data for " + scripts.length + " running scripts");
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
	
	if ( scripts.length > max_runs ) {
		http_response.end("Too busy");		
		return;
	};
	
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

/******************************************************************************
* Actually extracts the code and then checks config to determine whether we 
* should run this as if on a developer machine or whether to run as if on an
* actual server.
* TODO: Refactor executor to be two classes one for local and one for lxc
******************************************************************************/
function execute(http_req, http_res, request_data) {
	http_res.writeHead(200, {'Content-Type': 'text/plain'});
	
	script = { run_id : request_data.run_id, 
			 	scraper_name : request_data.scrapername,
			    scraper_guid : request_data.scraperid,
			 	query : request_data.urlquery, 
			 	pid: -1, 
				vm: '', 
				language: request_data.language || 'python',
				ip: ''};
	
	if ( ! use_lxc ) {
		// Execute the code locally using the relevant file (exec.whatever)
		var tmpfile = '/tmp/script.' + util.extension_for_language(script.language);
		fs.writeFile(tmpfile, request_data.code, function(err) {
	   		if(err) {
				r = {"error":"Failed to write file to local disk", "headers": http_req.headers , "lengths":  -1 };
				http_res.end( JSON.stringify(r) );
				return;				
	   		} else {

				http_req.connection.addListener('close', function () {
					// Let's handle the user quitting early
					delete scripts[script.run_id];					
					console.log(' - Connection was closed');
			    });


				args = ['--script',tmpfile,'--ds','127.0.0.1:9005','--scrapername',script.scraper_name, '--runid', script.run_id]
				exe = './exec.' + util.extension_for_language(script.language);

				e = spawn(exe, args, { env: util.env_for_language(script.language, extra_path) });
				script.pid = e.pid;
				script.ip = '127.0.0.1';
				
				scripts[ script.run_id ] = script;
				scripts_ip[ script.ip ] = script;
			
				console.log( "Script " + script.run_id + " executed with " + script.pid );

				e.stdout.on('data', function (data) {
					write_to_caller( http_res, data );
				});
				e.stderr.on('data', function (data) {
					write_to_caller( http_res, data );
				});				
				e.on('exit', function (code) {
	 				console.log('child process exited with code ' + code);
					delete scripts[script.run_id];
					delete scripts_ip[ script.ip ];
					
	 				console.log('child process removed from script list');					
					http_res.end();
				});
	     	}
		}); // end of writefile
	} else {
		
		// Use LXC to allocate us an instance and run with it
		var res = lxc.exec( script, code );
		if ( res ) {
			http_res.end( res );
			return;				
		}
		
	}


	
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


/******************************************************************************
* Write the response to the caller, or in this case write it back down the long
* lived socket that connected to us.
******************************************************************************/
function write_to_caller(http_res, output) {
	msg = output.toString();
	r = { 'message_type':'console', 'content': msg  };
	http_res.write( JSON.stringify(r) + "\n");
}
/*
 if streamprintsin in rback:
                srecprints = streamprintsin.recv(8192)   # returns '' if nothing more to come
                printsbuffer.append(srecprints)
                if not srecprints or srecprints[-1] == '\n':
                    line = "".join(printsbuffer)
                    if line:
                        jsonoutputlist.append(json.dumps({ 'message_type':'console', 'content':saveunicode(line) }))
                    del printsbuffer[:]
                if not srecprints:
                    streamprintsin.close()
                    rlist.remove(streamprintsin)

            # valid json objects coming in from file descriptor 3
            if streamjsonsin in rback:
                srecjsons = streamjsonsin.recv(8192)
                if srecjsons:
                    ssrecjsons = srecjsons.split("\n")
                    jsonsbuffer.append(ssrecjsons.pop(0))
                    while ssrecjsons:
                        jsonoutputlist.append("".join(jsonsbuffer))
                        del jsonsbuffer[:]
                        jsonsbuffer.append(ssrecjsons.pop(0))
                else:
                    streamjsonsin.close()
                    rlist.remove(streamjsonsin)

            # output the sequence of valid json objects to the dispatcher delimited by \n
            try:
                for jsonoutput in jsonoutputlist:
                    self.connection.sendall(jsonoutput + '\n')

        return { 'message_type':'executionstatus', 'content':'runcompleted', 
                 'elapsed_seconds' : int(ostimes2[4] - ostimes1[4]), 'CPU_seconds':int(ostimes2[0] - ostimes1[0]) }

*/