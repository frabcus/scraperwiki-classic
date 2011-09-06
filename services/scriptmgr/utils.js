/******************************************************************************
* utils.js
*
* Utility functions for working with the processes locally
******************************************************************************/
var path  = require('path');
var fs = require('fs'),
_ = require('underscore');

/******************************************************************************
* Write the response to the caller, or in this case write it back down the long
* lived socket that connected to us.
******************************************************************************/
exports.write_to_caller = function(http_res, output) {
	var msg = output.toString();
	var parts = msg.split("\n");	

	// Hacky solution to making sure HTML is sent all on one line for now.
	sub = msg.substring(0,100);
	if ( sub.indexOf('>') >= 0  && sub.indexOf('<') >= 0 && sub.toLowerCase().indexOf('html') >= 0) {
		r = { 'message_type':'console', 'content': msg  };
		http_res.write( JSON.stringify(r) + "\n");
		return;
	}
	

	http_res.write(  JSON.stringify( { 'message_type':'console', 'content': msg  } ) + "\n") );

/*	for (var i=0; i < parts.length; i++) {
		if ( parts[i].length > 0 ) {
			try {
				s = JSON.parse(parts[i]);
				if ( s && typeof(s) == 'object' ) {
					http_res.write( parts[i] + "\n");
					continue;
				} 
			}catch(err) {
				//
			}
			
			http_res.write( JSON.stringify( { 'message_type':'console', 'content': parts[i]  } ) + "\n");
		}
	};*/
}


var streamLogger = require('streamlogger');
var logger;

/******************************************************************************
* Set up logging to the specific file with the level where level = 
* debug: 0, info: 1, warn: 2, fatal: 3  
******************************************************************************/
exports.setup_logging = function( logfile, level ) {
	logger = new streamLogger.StreamLogger( logfile );	
	logger.level = level;
	
	process.on('SIGHUP', function () {
  		logger.reopen();
	});
	
	exports.log = logger;
};



var exts = {
	'python' : 'py', 
	'ruby'   : 'rb', 	
	'php'   : 'php', 		
	'javascript' : 'js',
}

/******************************************************************************
* Silly look up to get the extension for the language we are executing
******************************************************************************/
exports.extension_for_language = function( lang ) {
	return exts[lang];
};

/******************************************************************************
* Works out what environment variables we want to pass to the script
******************************************************************************/
exports.env_for_language = function( lang, extra_path ) {
	var ep = path.join(extra_path, lang)
	
	if ( lang == 'python' ) {
		return {PYTHONPATH: ep, PYTHONUNBUFFERED: 'true'};
	} else if ( lang == 'ruby') {
		return { RUBYLIB: ep };		
	} else if ( lang == 'php') {
		return { PHPPATH: ep};		
	} else if ( lang == 'javascript' ) {
		return { NODE_PATH: process.env.NODE_PATH + ":" + ep };
	}	
};

				
exports.dumpError = function(err) {
  if (typeof err === 'object') {
    if (err.message) {
      util.log.warn('Message: ' + err.message)
    }
    if (err.stack) {
      util.log.warn(err.stack);
    }
  } else {
    console.log('dumpError :: argument is not an object');
  }
}



/******************************************************************************
* Empty all files (and created folders) within a specific directory
******************************************************************************/
exports.cleanup = function(filep) {
	removeDirForce(filep);
	logger.debug('Cleanup up folder ' + filep);
}

function removeDirForce(filep) {
	var files = fs.readdirSync(filep);
    _.each(files, function(file) {
    	var filePath = path.join(filep,file);
		var stats = fs.statSync(filePath);
		if (stats.isDirectory()) {
			removeDirForce(filePath);
		} 
		if (stats.isFile()) {
			fs.unlinkSync(filePath);
		}
	});
}