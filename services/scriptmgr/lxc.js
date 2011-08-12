/******************************************************************************
* lxc.js
*
* 
* 
******************************************************************************/
var exec = require('./executor');
var _    = require('underscore')._;

// We will have up to X virtual machines where X is defined in config. Ideally

var vms = [ ];

exports.init = function(count) {

	vms = _.map( _.range(1, count), function(num){ return 'vm' + num; } );	
};

