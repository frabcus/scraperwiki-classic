/******************************************************************************
* registry.js
*
* The main registry of run_id -> readers + writers
******************************************************************************/

var max_read  = 10;
var max_write = 10;

var connections = [  ];

exports.ConnectionTypeEnum = ConnectionTypeEnum = {
    READER : 0,
    WRITER : 1
};


/******************************************************************************
* 
******************************************************************************/
exports.set_max = function( read, write ) {
	max_read = read;
	max_write = write;
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
	if ( type == ConnectionTypeEnum.READER ) {
		
		if ( obj.Readers.length >= max_read ) 
			return false;
		obj.Readers.push( socket );
		
	} else if ( type == ConnectionTypeEnum.WRITER ) {
		
		if ( obj.Writers.length >= max_write ) 
			return false;
		obj.Writers.push( socket );
		
	}
	
	return true;
}

function create_binding( k ) {
	return {
		Key: k,
		Readers: [],
		Writers: []
	}
}