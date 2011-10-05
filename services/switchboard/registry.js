/******************************************************************************
* registry.js
*
* The main registry of run_id -> readers + writers
******************************************************************************/

var connections = [  ];

exports.ConnectionTypeEnum = {
    READER : 0,
    WRITER : 1
}

/******************************************************************************
* 
******************************************************************************/
exports.bind = function( key, socket, type ) {
	var obj = connections[key] || null;
	if ( obj == null ) {
		obj = create_binding(key);
	} 
	
	connections[key] = obj;
	// set the relevant connection if we have space
	
	return false;
}

function create_binding( k ) {
	return {
		Key: k,
		Readers: [],
		Writers: []
	}
}