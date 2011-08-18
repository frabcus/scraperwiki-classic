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
var util  = require('./utils.js');
var path  = require('path');

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
	return allocate_vm( script );
};


/******************************************************************************
* Kill the LXC instance that is currently running the provided script
******************************************************************************/
exports.kill = function( script ) {
	var vm = vms_by_runid[ script.run_id ];
	if ( vm ) {
		// trigger an lxc-kill
		// lxc-stop -n 'vm'
		e = spawn('lxc-stop', ['-n', vm]);

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
	var folder = path.join(root_folder, name);
	
	num = parseInt( name.substring(2) );
	
	// TODO: Fix me
	ctx = {'name': name, 'ip': '10.0.1.' + (num + 1).toString() }

	// Create the config file so that we can create our VM
	Mu.render('./templates/config.tpl', ctx, {}, function (err, output) {
	  if (err) {
	  	throw err;
	  }

  	  var buffer = '';

  	  output.addListener('data', function (c) {buffer += c; })
      output.addListener('end', function () {
	  	var path = path.join(folder,'/config');
		
		fs.writeFile(path, buffer, function(err) {
		    if(err) {
		        sys.puts(err);
		    } else {
				// call lxc-create -n name -f folder/config
			 	e = spawn('lxc-create', ['-n', name, '-f', path]);
				e.on('exit', function (code, signal) {
						util.log.debug('LXC-Create exited with code ' + code);					
				});
			
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
* Release the VM using the provided script. 
*****************************************************************************/
function release_vm ( script, name ) {
	var k;
	
	for ( var key in vms ) {
		var vm = vms[key];
		k = key;
		if ( ! vm.script.run_id == script.run_id ) {
			v = vm;
			break;
		};
	}

	if ( ! v ) {
		return;
	};

	// Remove it from the two lookup tables
	delete vms_by_runid[ script.run_id ]
	delete vms_by_ip[ script.ip ]
	
	v.running = false;
	v.script = null;
	vms[k] = v;
}

/*****************************************************************************
* Allocate a vm to the calling script.  We will check to find one that isn't
* running and either allocate it or return null if none are found.
*
* TODO: Fix this and use filter
******************************************************************************/
function allocate_vm ( script ) {
	var v, k;
	for ( var key in vms ) {
		var vm = vms[key];
		k = key;
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
	vms[k] = v;
	return v
}
