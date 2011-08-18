/******************************************************************************
* scriptmgr specific settings. We need to have different versions of these 
* based on the environment. Expect that on live servers this will be ignored 
* in preference to a version stored in /etc
*
* Random thought: Can we fetch this from the django app?
******************************************************************************/
exports.settings =
{ 
	devmode: true, 
	port: 9001, 
	vm_count: 50, 
	extra_path: '../../scraperlibs',
	dataproxy: '127.0.0.1:9003',
	httpproxy: '127.0.0.1:9005',
	listen_on: '127.0.0.1',
	logfile: '/var/log/scraperwiki/scriptmgr.log',
	loglevel: 0, // debug: 0, info: 1, warn: 2, fatal: 3  
};
