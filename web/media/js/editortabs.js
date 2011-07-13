var scrollPositions = { 'console':0, 'data':0, 'sources':0, 'chat':0 }; 
var outputMaxItems = 400;
var sTabCurrent = ''; 
var sChatTabMessage = 'Chat'; 

// information handling who else is watching and editing during this session
var editingusername = "";  // primary editor
var loggedinusers = [ ];   // all people watching
var loggedineditors = [ ]; // list of who else is here and their windows open who have editing rights
var iselectednexteditor = 1; 
var nanonymouseditors = 0; // number of anonymous editors
var countclientsconnected = 0; 
var chatname = "";         // special in case of Anonymous users (yes, this unnecessarily gets set every time we call recordEditorStatus)
var clientnumber = -1;     // allocated by twister for this window, so we can find it via django
var chatpeopletimes = { }; // last time each person made a chat message

// these actually get set by the server
var servernowtime = new Date(); 
var earliesteditor = servernowtime; 
var lasttouchedtime = undefined; 


function cgiescape(text) 
{
    if (typeof text == 'number')
        return String(text); 
    if (typeof text != 'string')
        return "&lt;NONSTRING "+(typeof text)+"&gt;"; // should convert on server
    return (text ? text.replace(/&/g, '&amp;').replace(/</g, '&lt;') : "");
}

// some are implemented with tables, and some with span rows.  
function setTabScrollPosition(sTab, command) 
{
    divtab = '#output_' + sTab; 
    contenttab = '#output_' + sTab; 

    if ((sTab == 'console') || (sTab == 'sources')) 
    {
        divtab = '#output_' + sTab + ' div';
        contenttab = '#output_' + sTab + ' .output_content';
    }

    if (command == 'hide')
        scrollPositions[sTab] = $(divtab).scrollTop();
    else 
    {
        if (command == 'bottom')
            scrollPositions[sTab] = $(contenttab).height()+$(divtab)[0].scrollHeight; 
        $(divtab).animate({ scrollTop: scrollPositions[sTab] }, 0);
    }
}

function clearOutput() 
{
    $('#output_console div').html('');
    $('#output_sources div').html('');
    $('#output_data table').html('');
    $('.editor_output div.tabs li.console').removeClass('new');
    $('.editor_output div.tabs li.data').removeClass('new');
    $('.editor_output div.tabs li.sources').removeClass('new');
}

//Write to console/data/sources
function writeToConsole(sMessage, sMessageType, iLine) 
{
    // if an exception set the class accordingly
    var sShortClassName = '';
    var sLongClassName = 'message_expander';
    var sExpand = '...more'

    var sLongMessage = undefined; 
    if (sMessageType == 'httpresponseheader') 
        sShortClassName = 'exception';

    if (sMessageType == 'exceptiondump') 
        sShortClassName = 'exception';

    var escsMessage = cgiescape(sMessage); 
    if (sMessageType == 'exceptionnoesc') {
        sShortClassName = 'exception';
        escsMessage = sMessage; // no escaping
    }
    else if (sMessage.length > 110) {
        sLongMessage = sMessage; 
        escsMessage = cgiescape(sMessage.replace(/^\s+|\s+$/g, "").substring(0, 100)); 
    }

    //create new item
    var oConsoleItem = $('<span></span>');
    oConsoleItem.addClass('output_item');
    oConsoleItem.addClass(sShortClassName);
    
    oConsoleItem.html(escsMessage); 

    if(sLongMessage != undefined) 
    {
        oMoreLink = $('<a href="#"></a>');
        oMoreLink.addClass('expand_link');
        oMoreLink.text(sExpand)
        oMoreLink.longMessage = sLongMessage;
        oConsoleItem.append(oMoreLink);
        oMoreLink.click(function() { showTextPopup(sLongMessage); });
    }

    // add clickable line number link
    if (iLine != undefined) {
        oLineLink = $('<a href="#">Line ' + iLine + ' - </a>'); 
        oConsoleItem.prepend(oLineLink);
        oLineLink.click( function() { 
            codeeditor.selectLines(codeeditor.nthLine(iLine), 0, codeeditor.nthLine(iLine + 1), 0); 
        }); 
    }

    
    //remove items if over max
    while ($('#output_console div.output_content').children().size() >= outputMaxItems) 
        $('#output_console div.output_content').children(':first').remove();

    //append to console
    $('#output_console div.output_content').append(oConsoleItem);
    $('.editor_output div.tabs li.console').addClass('new');

    setTabScrollPosition('console', 'bottom'); 
};



function writeToSources(sUrl, lmimetype, bytes, failedmessage, cached, cacheid, ddiffer, fetchtime) 
{
    //remove items if over max
    while ($('#output_sources div.output_content').children().size() >= outputMaxItems) 
        $('#output_sources div.output_content').children(':first').remove();

    // normalize the mimetypes
    if (lmimetype == undefined)
        lmimetype = "text/html"; 
    else if (lmimetype == "text/html")
        ; 
    else if (lmimetype == "application/json")
        lmimetype = "text/json"; 

    //append to sources tab
    var smessage = [ ]; 
    var alink = '<a href="' + sUrl + '" target="_new">' + sUrl.substring(0, 100) + '</a>'; 
    if ((failedmessage == undefined) || (failedmessage == ''))
    {
        smessage.push('<span class="bytesloaded">', bytes, 'bytes loaded</span>, '); 
        if (lmimetype.substring(0, 5) != "text/") 
            smessage.push("<b>"+lmimetype+"</b>"); 

        // this is the orange up-arrow link that doesn't work because something wrong in the server, so hide it for now
        //if (cacheid != undefined)
        //    smessage.push('<a id="cacheid-'+cacheid+'" title="Popup html" class="cachepopup">&nbsp;&nbsp;</a>'); 

        if (cached == 'True')
            smessage.push('(from cache)'); 
    }
    else
        smessage.push(failedmessage); 
    if (ddiffer == "True")
        smessage.push('<span style="background:red"><b>BAD CACHE</b></span>, '); 
    if (fetchtime != undefined)
        smessage.push('<span class="">response time: ', Math.round(fetchtime*1000), 'ms</span>, '); 

    smessage.push(alink); 

    $('#output_sources div.output_content').append('<span class="output_item">' + smessage.join(" ") + '</span>')
    $('.editor_output div.tabs li.sources').addClass('new');
    
    if (cacheid != undefined)  
        $('a#cacheid-'+cacheid).click(function() { popupCached(cacheid, lmimetype); return false; }); 

    setTabScrollPosition('sources', 'bottom'); 
}


function writeToData(aRowData) 
{
    while ($('#output_data table.output_content tbody').children().size() >= outputMaxItems) 
        $('#output_data table.output_content tbody').children(':first').remove();

    var oRow = $('<tr></tr>');

    $.each(aRowData, function(i){
        var oCell = $('<td></td>');
        oCell.html(cgiescape(aRowData[i]));
        oRow.append(oCell);
    });

    $('#output_data table.output_content').append(oRow);  // oddly, append doesn't work if we add tbody into this selection
    setTabScrollPosition('data', 'bottom'); 
    $('.editor_output div.tabs li.data').addClass('new');
}

function writeToSqliteData(command, val1, lval2) 
{
    while ($('#output_data table.output_content tbody').children().size() >= outputMaxItems) 
        $('#output_data table.output_content tbody').children(':first').remove();

    var row = [ ]; 
    row.push('<tr><td><b>'+cgiescape(command)+'</b></td>'); 
    if (val1)
        row.push('<td>'+cgiescape(val1)+'</td>'); 
    if (lval2)
    {
        for (var i = 0; i < lval2.length; i++)
            row.push('<td>'+cgiescape(lval2[i])+'</td>'); 
    }
    row.push('</tr>'); 

    $('#output_data table.output_content').append($(row.join("")));  
    setTabScrollPosition('data', 'bottom'); 
    $('.editor_output div.tabs li.data').addClass('new');
}

function writeToChat(seMessage, sechatname) 
{
    while ($('#output_chat table.output_content tbody').children().size() >= outputMaxItems) 
        $('#output_chat table.output_content tbody').children(':first').remove();

    var oRow = $('<tr><td>' + (sechatname ? sechatname + ": " : "") + seMessage + '</td></tr>');
    $('#output_chat table.output_content').append(oRow);
    setTabScrollPosition('chat', 'bottom'); 
    $('.editor_output div.tabs li.chat').addClass('new');

    if (sechatname && (sechatname != chatname))
    {
            // currently highlights when there is more than a minute gap.  But could be longer
        if ((chatpeopletimes[sechatname] == undefined) || ((servernowtime.getTime() - chatpeopletimes[sechatname].getTime())/1000 > 60))
        {
            chatpeopletimes[sechatname] = servernowtime; 
            if (sTabCurrent != 'chat')
                $('.editor_output div.tabs li.chat').addClass('chatalert');
        }
    }
}

//show tab
function showTab(sTab)
{
    setTabScrollPosition(sTabCurrent, 'hide'); 
    $('.editor_output .info').children().hide();
    $('.editor_output .controls').children().hide();        
    
    $('#output_' + sTab).show();
    $('#controls_' + sTab).show();
    sTabCurrent = sTab; 

    $('.editor_output div.tabs ul').children().removeClass('selected');
    $('.editor_output div.tabs li.' + sTab).addClass('selected');
    $('.editor_output div.tabs li.' + sTab).removeClass('new');
    if (sTab == 'chat')
        $('.editor_output div.tabs li.chat').removeClass('chatalert');
    
    setTabScrollPosition(sTab, 'show'); 
}

