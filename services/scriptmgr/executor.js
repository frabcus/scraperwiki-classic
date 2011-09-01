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
var path  = require('path');

var use_lxc = true;
var extra_path;
var code_folder = '/tmp';

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
exports.init = function( settings ) {
	use_lxc = ! settings.devmode;

	if ( use_lxc ) {
		lxc.init(settings.vm_count, settings.mount_folder);
	}

	if ( settings.devmode ) {
		httpproxy = settings.httpproxy;
	};

	code_folder = settings.code_folder;
	dataproxy = settings.dataproxy;
	extra_path = settings.extra_path;
	max_runs = settings.vm_count;
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
			
  			util.log.debug('Killed process PID: ' + pid);					
			return true;
		};
	} else {
		
	}
	
	return false;
}

exports.known_ips = function() {
	return scripts_ip;
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
	
	util.log.debug("+ Get status returning data for " + scripts.length + " running scripts");
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

	// Handle the request being closed by the client	
	http_request.on("close", function() {
		util.log.debug('Client killed the connection')
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
			util.log.warn('Incomplete incoming message');			
			return;
		};

		execute(http_request, http_response, body);
		util.log.debug('Done calling execute');		
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
		util.dumpError( err );
	}
	
	script = { run_id : request_data.runid, 
			 	scraper_name : request_data.scrapername || "",
			    scraper_guid : request_data.scraperid,
			 	query : request_data.urlquery, 
			 	pid: -1, 
				vm: '', 
				language: request_data.language || 'python',
				ip: '',
				response: http_res,
				black: request_data.black || '',
				white: request_data.white || '',
				permissions: request_data.permissions || []  };
	
	if ( ! use_lxc ) {
		// Execute the code locally using the relevant file (exec.whatever)
		var tmpfile = path.join( code_folder, "script." + util.extension_for_language(script.language) );
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
					util.log.debug( args );
				} else {
					args = ['--script',tmpfile,'--ds', dataproxy, '--runid', script.run_id]
					if ( script.scraper_name ) {
						args.push('--scrapername')
						args.push( script.scraper_name )
					}
					util.log.debug( args );
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
					if ( script ) {
						delete scripts[script.run_id];					
						delete scripts_ip[ script.ip ];					
					}
			    });
			
				util.log.debug( "Script " + script.run_id + " executed with " + script.pid );

				e.stdout.on('data', function (data) {
					handle_process_output( http_res, data, true );
				});
				
				e.stderr.on('data', function (data) {
					handle_process_output( http_res, data, false );					
				});				
				
				e.on('exit', function (code, signal) {
					if ( code == null )
						util.log.debug('child process exited badly, we may have killed it');
					else 
	 					util.log.debug('child process exited with code ' + code);					
					if ( script ) {
						delete scripts[script.run_id];
						delete scripts_ip[ script.ip ];
					}
					
	 				util.log.debug('child process removed from script list');					

					var endTime = new Date();
					elapsed = (endTime - startTime) / 1000;

					// 'CPU_seconds': 1, Temporarily removed
        			res =  { 'message_type':'executionstatus', 'content':'runcompleted', 
                 'elapsed_seconds' : elapsed, 'exit_status': 0 };
					http_res.end( JSON.stringify( res ) + "\n" );
										
					util.log.debug('Finished writing responses');
				});
	     	}
		}); // end of writefile
	} else {
		
		// Use LXC to allocate us an instance and run with it
		var res = lxc.exec( script, request_data.code );
		if ( res == null ) {
			var r = {"error": "No virtual machines available"}
			http_res.end( JSON.stringify(r) );
			return;				
		}
		console.log( 'Running on ' + res );		
				
		var extension = util.extension_for_language(script.language);
		var tmpfile = path.join(lxc.code_folder(res), "script." + extension );
		fs.writeFile(tmpfile, request_data.code, function(err) {
	   		if(err) {
				r = {"error":"Failed to write file to local disk", "headers": http_req.headers , "lengths":  -1 };
				http_res.end( JSON.stringify(r) );
				return;				
	   		} 

			util.log.debug('File written to ' + tmpfile );
			
			var startTime = new Date();		

			// Pass the data proxy and runid to the script that will trigger the exec.py
			var cfgpath = '/mnt/' + res + '/config';
						
	 		e = spawn('/usr/bin/lxc-execute', ['-n', res, '-f', cfgpath, "/home/startup/run" + extension + ".sh",dataproxy, script.run_id ]);
	
			script.vm = res;
			script.ip = lxc.ip_for_vm(res);
				
			scripts[ script.run_id ] = script;
			scripts_ip[ script.ip ] = script;
	
			e.stdout.on('data', function (data) {
				handle_process_output( http_res, data, true );
			});
			e.stderr.on('data', function (data) {
				handle_process_output( http_res, data, false );					
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
			
				util.log.debug('child process removed from script list');					

				var endTime = new Date();
				elapsed = (endTime - startTime) / 1000;

				// 'CPU_seconds': 1, Temporarily removed
	      		res =  { 'message_type':'executionstatus', 'content':'runcompleted', 
	               'elapsed_seconds' : elapsed, 'exit_status': 0 };
				if ( script && script.response ) {
					console.log('Done');
					script.response.end( JSON.stringify( res ) + "\n" );
				}
								
				lxc.release_vm( script, res );
								
				util.log.debug('Finished writing responses');
			});
		});
	}
}


/******************************************************************************
* Makes sure the process output goes back to the client
******************************************************************************/
function handle_process_output(http_res, data, stdout) {
	if (stdout) {
		util.write_to_caller( http_res, data, true );				
		return;
	} 
	try 
	{
		s = JSON.parse(data);
		if ( s ) {
			http_res.write( data );
			sent = true;
		}
	}
	catch(err) 
	{
		util.write_to_caller( http_res, data, false);			
	}		
}


