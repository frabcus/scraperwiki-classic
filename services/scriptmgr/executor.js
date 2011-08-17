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
var sys = require('sys');
var spawn = require('child_process').spawn;

var use_lxc = true;
var extra_path;

// A list of all of the currently running scripts
var scripts = [ ];
var scripts_ip = [ ];
var max_runs = 100;
var dataproxy = '';
var httpproxy;

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

	if ( config.devmode ) {
		httpproxy = config.httpproxy;
	};

	dataproxy = config.dataproxy;
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
			s = scripts[run_id];
			delete scripts[run_id];
			delete scripts_ip[s.ip];
			
  			console.log('Killed process PID: ' + pid);					
			return true;
		};
	} else {
		
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
	if ( details.ip ) {
		return scripts_ip[details.ip];
	} else if ( details.runid ) {
		return scripts[details.runid];
	}
	
	return null;
}


/******************************************************************************
* Works out from the incoming request what it is that needs executing, if 
* we can find it from the post data.
******************************************************************************/
exports.run_script = function( http_request, http_response ) {
	
	http_request.setEncoding( 'utf8');
	
	if ( scripts.length > max_runs ) {
		r = {"error":"Too busy", "headers": http_request.headers , "lengths":  -1 };
		http_response.end( JSON.stringify(r) );
		return;
	};

	console.log('Setting up close event etc');
	
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
		if ( body == undefined || body.length == 0 || body.length != len ) {
			r = {"error":"incoming message incomplete", "headers": http_request.headers , "lengths":  len.toString() };
			http_response.end( JSON.stringify(r) );
			console.log('Incomplete incoming message');			
			return;
		};

		execute(http_request, http_response, body);
		console.log('Done calling execute');		
	});
		
};

/******************************************************************************
* Actually extracts the code and then checks config to determine whether we 
* should run this as if on a developer machine or whether to run as if on an
* actual server.
* TODO: Refactor executor to be two classes one for local and one for lxc
******************************************************************************/
function execute(http_req, http_res, raw_request_data) {
	http_res.writeHead(200, {'Content-Type': 'text/plain'});
	
	try {
		request_data = JSON.parse( raw_request_data );
	} catch ( err )
	{
		dumpError( err );
	}
	
	script = { run_id : request_data.runid, 
			 	scraper_name : request_data.scrapername || "",
			    scraper_guid : request_data.scraperid,
			 	query : request_data.urlquery, 
			 	pid: -1, 
				vm: '', 
				language: request_data.language || 'python',
				ip: '',
				response: http_res };
	
	if ( ! use_lxc ) {
		// Execute the code locally using the relevant file (exec.whatever)
		var tmpfile = '/tmp/script.' + util.extension_for_language(script.language);
		fs.writeFile(tmpfile, request_data.code, function(err) {
	   		if(err) {
				r = {"error":"Failed to write file to local disk", "headers": http_req.headers , "lengths":  -1 };
				http_res.end( JSON.stringify(r) );
				return;				
	   		} else {
				if ( script.language == 'ruby') {
					args = ['--script=' + tmpfile,'--ds=' + dataproxy, '--runid=' + script.run_id]
					if ( script.scraper_name ) {
						args.push('--scrapername=' + script.scraper_name )
					}
					console.log( '********************** RUBY' );					
					console.log( args );
				} else {
					args = ['--script',tmpfile,'--ds', dataproxy, '--runid', script.run_id]
					if ( script.scraper_name ) {
						args.push('--scrapername')
						args.push( script.scraper_name )
					}
					console.log( args );
				}
				
				exe = './scripts/exec.' + util.extension_for_language(script.language);

				var startTime = new Date();
				var environ = util.env_for_language(script.language, extra_path) 
				if (httpproxy) {
					environ['http_proxy'] = 'http://' + httpproxy;
				};
				
				e = spawn(exe, args, { env: environ });
				script.pid = e.pid;
				script.ip = '127.0.0.1';
				
				scripts[ script.run_id ] = script;
				scripts_ip[ script.ip ] = script;

				http_req.connection.addListener('close', function () {
					// Let's handle the user quitting early it might be a KILL
					// command from the dispatcher
					if ( e ) e.kill('SIGKILL');
					console.log(' - Sent kill signal');					
					if ( script ) {
						delete scripts[script.run_id];					
						delete scripts_ip[ script.ip ];					
					}
					console.log(' - Connection was closed');
			    });
			
				console.log( "Script " + script.run_id + " executed with " + script.pid );

				e.stdout.on('data', function (data) {
					write_to_caller( http_res, data, true );					
				});
				
				e.stderr.on('data', function (data) {
					try {
						s = JSON.parse(data);
						if ( s ) {
							console.log('Writing ' + data)
							http_res.write( data );
						}
					}catch(err) {
						write_to_caller( http_res, data, false);
					}					
				});				
				
				e.on('exit', function (code, signal) {
					if ( code == null )
	 					console.log('child process exited badly, we may have killed it');
					else 
	 					console.log('child process exited with code ' + code);					
					if ( script ) {
						delete scripts[script.run_id];
						delete scripts_ip[ script.ip ];
					}
					
	 				console.log('child process removed from script list');					

					var endTime = new Date();
					elapsed = (endTime - startTime) / 1000;
// signal if not null
        			res =  { 'message_type':'executionstatus', 'content':'runcompleted', 
                 'elapsed_seconds' : elapsed, 'CPU_seconds': 1, 'exit_status': 0 };
					http_res.end( JSON.stringify( res ) + "\n" );
										
					console.log('Finished writing responses');
				});
	     	}
		}); // end of writefile
	} else {
		
		// Use LXC to allocate us an instance and run with it
		/*
		var res = lxc.exec( script, code );
		if ( res ) {
			http_res.end( res );
			return;				
		}
		*/
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
function write_to_caller(http_res, output, isstdout) {
	var msg = output.toString();
	var parts = msg.split("\n");	

	// Hacky solution to making sure HTML is sent all on one line.
	sub = msg.substring(0,100);
	if ( sub.indexOf('html') >= 0 && sub.indexOf('>') >= 0  && sub.indexOf('<') >= 0) {
		r = { 'message_type':'console', 'content': msg  };
		console.log(r);
		http_res.write( JSON.stringify(r) + "\n");
		return;
	}
	

	for (var i=0; i < parts.length; i++) {
		if ( parts[i].length > 0 ) {
			try {
				// Removing the need for the extra FD by checking if we can parse
				// the JSON
				s = JSON.parse(parts[i]);
				if ( s ) {
					console.log( s.message_type );
					http_res.write( parts[i] );
				}
				continue;
			}catch(err) {
				//
			}
			
			r = { 'message_type':'console', 'content': parts[i]  };
			console.log(r);
			http_res.write( JSON.stringify(r) + "\n");
		}
	};
}


function dumpError(err) {
  if (typeof err === 'object') {
    if (err.message) {
      console.log('\nMessage: ' + err.message)
    }
    if (err.stack) {
      console.log('\nStacktrace:')
      console.log('====================')
      console.log(err.stack);
    }
  } else {
    console.log('dumpError :: argument is not an object');
  }
}