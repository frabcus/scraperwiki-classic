/******************************************************************************
* lxc.js
*
* Abstracts running the provided code through an lxc instance. We make sure at
* initialisation that all of the LXCs that we expect are created and running.
* 
******************************************************************************/
var _    = require('underscore')._;
var mu   = require('mu');
var fs   = require('fs');
var spawn = require('child_process').spawn;

// All of our virtual machines
var vms = [ ]; // vm name -> objects


var vms_by_ip    = [ ]; // maps of ip -> vm name
var vms_by_runid = [ ]; // maps of runid -> vm name

var root_folder = '';

/******************************************************************************
* 
******************************************************************************/
exports.init = function(count, lxc_root_folder) {
	root_folder = lxc_root_folder;
		
	vms = _.map( _.range(1, count), function(num){ return 'vm' + num; } );	
	vms = _.invoke( vms, 'create_vm' );
};


/******************************************************************************
* Execute the provided code on an lxc instance if we can get one.
******************************************************************************/
exports.exec = function(script, code) {
	// execute lxc-execute on a vm, after we've been allocated on
	vm = allocate_vm( script );
	if ( ! vm ) {
		r = {"error":"No VM resource is available", "headers": '' , "lengths":  -1 };
		return JSON.stringify(r);
	}
	
	// 
	
	
};


/******************************************************************************
* Kill the LXC instance that is currently running the provided script
******************************************************************************/
exports.kill = function( script ) {
	vm = vms_by_runid[ script.run_id ];
	if ( vm ) {
		// trigger an lxc-kill
		// lxc-stop -n 'vm'

		// Clean up indices
		delete vms_by_run_id[ script.run_id ];		
		delete vms_by_ip[ script.ip ];
	}
	return false;
};


/*****************************************************************************
* Create a new VM based on newly created config files - if not already created
******************************************************************************/
function create_vm ( name ) {

	var v = {
		'name': name,
		'running': false,
		'script': null,		
	}
	
	// if name exists then just return, otherwise integrate templates and then
	// lxc-create.  Bear in mind that currently (and naffly) the IP address 
	// will be the vm number + 1 (as vm0 has ip 10.0.1.1 )

	// write config and fstab to ...	
	var folder = '/mnt/' + name;
	
	num = parseInt( name.substring(2) );
	
	ctx = {'name': name, 'ip': '10.0.1.' + (num + 1).toString() }

	// Create the config file so that we can create our VM
	Mu.render('./templates/config.tpl', ctx, {}, function (err, output) {
	  if (err) {
	  	throw err;
	  }

  	  var buffer = '';

  	  output.addListener('data', function (c) {buffer += c; })
      output.addListener('end', function () {
		var path = folder + '/config';
		
		fs.writeFile(path, buffer, function(err) {
		    if(err) {
		        sys.puts(err);
		    } else {
				// call lxc-create -n name -f folder/config
			 	//e = spawn(exe, args, { env: util.env_for_language(script.language, extra_path) });
				/*
				e.stdout.on('data', function (data) {
					write_to_caller( http_res, data );
				});
				e.stderr.on('data', function (data) {
					write_to_caller( http_res, data );
				});				
				e.on('exit', function (code) {
					delete scripts[script.run_id];
					delete scripts_ip[ script.ip ];
					
					http_res.end();
				});
				*/
		    }
		}); // end writefile
	  }); // addListener('end...
	}); // end Mu.render(...
	
	// Render the fstab for our vm
	Mu.render('./templates/fstab.tpl', ctx, {}, function (err, output) {
	  if (err) {
	  	throw err;
	  }

  	  var buffer = '';

  	  output.addListener('data', function (c) {buffer += c; })
      output.addListener('end', function () {
		var path = folder + '/fstab';
		
		fs.writeFile(path, buffer, function(err) {
		    if(err) {
		        sys.puts(err);
		    } 
		}); 	

	  });
	});	
	
	return v;
}


/*****************************************************************************
* Allocate a vm to the calling script.  We will check to find one that isn't
* running and either allocate it or return null if none are found.
******************************************************************************/
function allocate_vm ( script ) {
	var v;
	for ( var key in vms ) {
		vm = vms[key];
		if ( ! vm.running ) {
			v = vm;
			break;
		};
	}
	
	if ( ! v ) {
		return null;
	};
	
	v.running = true;
	v.script = script;
	return v
}
