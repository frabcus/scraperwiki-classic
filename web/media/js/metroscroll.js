
var metrolines;
var geoloc;
var maxevents;
var reqcount;
var lscript;
var speed;
var animtimer;
var baseurl; 

function init(lbaseurl)
{
	metrolines = new Array();
	geoloc = "lat=5&lon=6";
	maxevents = 6;
	reqcount = 0;
	lscript = null;
	speed = 1600;
    baseurl = lbaseurl; 
}

function callmetroweb(messid, limit)
{
	var llscript = document.createElement('script');
	reqcount++;
	var url = baseurl + "?" + geoloc + "&limit=" + limit + "&reqcount=" + reqcount;
	if (messid != 0)
		url += "&a0=c" + messid;

	llscript.setAttribute('src', url);
	llscript.setAttribute('type', 'text/javascript');
	llscript.setAttribute('id', 'script_' + reqcount);
	document.getElementsByTagName('head')[0].appendChild(llscript);

	return llscript;
}

function metroevent(obj)
{
	metrolines.push(obj);
}

function metroeventend(reqtid)
{
	// use this to clean the page
	var s = document.getElementById('script_' + reqtid);

	// to be removed from header
	if (s == lscript)
		lscript = null;
}

function eventclicked(messid)
{
	callmetroweb(messid, 0);
}

function pauseanimation()
{
	clearTimeout(animtimer);
}

function restartanimation()
{
	animtimer = setTimeout('loop();', speed);
}

function showevents()
{
	var t = document.getElementById("headlines");
	if (t.rows.length > maxevents)
		t.deleteRow(0);
	var obj = metrolines.shift();
	if (obj)
	{
		// append a row to table
		var r = t.insertRow(t.rows.length);

		// to pause and restart animation
		r.setAttribute('onmouseover', 'pauseanimation();');
		r.setAttribute('onmouseout',  'restartanimation();');

		// add cell with link
		var c = r.insertCell(0);
		c.innerHTML =
'<div id=' + obj.src + '>' +
'<a href="' + obj.url + '" target="_blank" onClick="eventclicked(' + obj.messid + ')">' + obj.title + '</a>';
'</div>';

;
	}
}

function loop()
{
	if ((metrolines.length == 0) && (lscript == null))
		lscript = callmetroweb(0, 6);

	showevents();
	restartanimation();
}
