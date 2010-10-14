$(document).ready(function() {

    //variables
    var pageIsDirty = true;
    var editor_id = 'id_code';
    var codeeditor = undefined;
    var codemirroriframe; // the iframe that needs resizing
    var codemirroriframeheightdiff = 0; // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var codemirroriframewidthdiff = 0;  // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var previouscodeeditorheight = 0; //$("#codeeditordiv").height() * 3/5;    // saved for the double-clicking on the drag bar
    var short_name = $('#short_name').val();
    var guid = $('#scraper_guid').val();
    var username = $('#username').val(); 
    var userrealname = $('#userrealname').val(); 
    var isstaff = $('#isstaff').val(); 
    var scraperlanguage = $('#scraperlanguage').val(); 
    var run_type = $('#code_running_mode').val();
    var codemirror_url = $('#codemirror_url').val();
    var wiki_type = $('#id_wiki_type').val(); 
    var viewrunurl = $('#viewrunurl').val(); 
    var activepreviewiframe = undefined; // used for spooling running console data into the preview popup
    var conn = undefined; // Orbited connection
    var bConnected = false; 
    var bSuppressDisconnectionMessages = false; 
    var buffer = "";
    var selectedTab = 'console';
    var outputMaxItems = 400;
    var popupStatus = 0
    var sTabCurrent = ''; 
    var sChatTabMessage = 'Chat'; 
    var scrollPositions = { 'console':0, 'data':0, 'sources':0, 'chat':0 }; 
    var receiverecordqueue = [ ]; 
    var receivechatqueue = [ ]; 
    var runID = ''; 

    // information handling who else is watching and editing during this session
    var earliesteditor = ""; 
    var editinguser = ""; 
    var bcansave = true; 
    var loggedineditors = [ ]; // list of who else is here and their windows open
    var nanonymouseditors = 0; 
    var chatname = ""   // special in case of Anonymous users

    var parsers = Array();
    var stylesheets = Array();
    var indentUnits = Array();
    var parserConfig = Array();
    var parserName = Array();

    $.ajaxSetup({
        timeout: 10000,
    });

    //constructor functions
    setupCodeEditor();
    setupMenu();
    setupOrbited();
    setupTabs();
    setupToolbar();
    setupResizeEvents();

    function setPageIsDirty(lpageIsDirty) {
        if (pageIsDirty == lpageIsDirty)
            return; 
        pageIsDirty = lpageIsDirty; 
        if (pageIsDirty && guid)
            $('#aCloseEditor1').css("font-style", "italic"); 
        else
            $('#aCloseEditor1').css("font-style", "normal"); 
    }

    //setup code editor
    function setupCodeEditor(){
        parsers['python'] = ['../contrib/python/js/parsepython.js'];
        parsers['php'] = ['../contrib/php/js/tokenizephp.js', '../contrib/php/js/parsephp.js', '../contrib/php/js/parsephphtmlmixed.js' ];
        parsers['ruby'] = ['../../ruby-in-codemirror/js/tokenizeruby.js', '../../ruby-in-codemirror/js/parseruby.js'];
        parsers['html'] = ['parsexml.js', 'parsecss.js', 'tokenizejavascript.js', 'parsejavascript.js', 'parsehtmlmixed.js']; 

        stylesheets['python'] = [codemirror_url+'contrib/python/css/pythoncolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['php'] = [codemirror_url+'contrib/php/css/phpcolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['ruby'] = [codemirror_url+'../ruby-in-codemirror/css/rubycolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['html'] = [codemirror_url+'/css/xmlcolors.css', codemirror_url+'/css/jscolors.css', codemirror_url+'/css/csscolors.css', '/media/css/codemirrorcolours.css']; 

        indentUnits['python'] = 4;
        indentUnits['php'] = 4;
        indentUnits['ruby'] = 2;
        indentUnits['html'] = 4;

        parserConfig['python'] = {'pythonVersion': 2, 'strictErrors': true}; 
        parserConfig['php'] = {'strictErrors': true}; 
        parserConfig['ruby'] = {'strictErrors': true}; 
        parserConfig['html'] = {'strictErrors': true}; 

        parserName['python'] = 'PythonParser';
        parserName['php'] = 'PHPHTMLMixedParser'; // 'PHPParser';
        parserName['ruby'] = 'RubyParser';
        parserName['html'] = 'HTMLMixedParser';

        // allow php to access HTML style parser
        parsers['php'] = parsers['html'].concat(parsers['php']);
        stylesheets['php'] = stylesheets['html'].concat(stylesheets['php']); 

        codeeditor = CodeMirror.fromTextArea("id_code", {
            parserfile: parsers[scraperlanguage],
            stylesheet: stylesheets[scraperlanguage],
            path: codemirror_url + "js/",
            domain: document.domain, 
            textWrapping: true,
            lineNumbers: true,
            indentUnit: indentUnits[scraperlanguage],
            readOnly: false,
            tabMode: "shift", 
            disableSpellcheck: true,
            autoMatchParens: true,
            width: '100%',
            parserConfig: parserConfig[scraperlanguage],
            enterMode: "flat", // default is "indent" (which I have found buggy),  also can be "keep"
            onChange: function ()  { setPageIsDirty(true); },

            // this is called once the codemirror window has finished initializing itself
            initCallback: function() {
                    codemirroriframe = codeeditor.frame // $("#id_code").next().children(":first"); (the object is now a HTMLIFrameElement so you have to set the height as an attribute rather than a function)
                    codemirroriframeheightdiff = codemirroriframe.height - $("#codeeditordiv").height(); 
                    codemirroriframewidthdiff = codemirroriframe.width - $("#codeeditordiv").width(); 
                    setupKeygrabs();
                    resizeControls('first');
                    setPageIsDirty(false); // page not dirty at this point
                } 
          });        
    }

    
    function setupOrbited() {
        TCPSocket = Orbited.TCPSocket;
        conn = new TCPSocket(); 
        conn.open('localhost', '9010'); 
        buffer = " "; 
        sChatTabMessage = 'Connecting...'; 
        $('.editor_output div.tabs li.chat a').html(sChatTabMessage);
    }
    
    //Setup Keygrabs

    function setupKeygrabs(){
        addHotkey('ctrl+r', sendCode);
        addHotkey('ctrl+s', saveScraper); 
        addHotkey('ctrl+d', viewDiff);
        addHotkey('ctrl+p', popupPreview); 
    };
    

    //Setup Menu
    function setupMenu(){
        $('#menu_tutorials').click(function(){
            $('#popup_tutorials').modal({
                 overlayClose: true, 
                 containerCss:{ borderColor:"#0ff", height:"80%", padding:0, width:"90%" }, 
                 overlayCss: { cursor:"auto" }
                });
        });
        $('form#editor').submit(function() { 
            saveScraper(); 
            return false; 
        })

        $('#chat_line').bind('keypress', function(eventObject) {
            var key = eventObject.charCode ? eventObject.charCode : eventObject.keyCode ? eventObject.keyCode : 0;
            var target = eventObject.target.tagName.toLowerCase();
            if (key === 13 && target === 'input') 
            {
                eventObject.preventDefault();
                if (bConnected) 
                    sendChat(); 
                return false; 
            }
            return true; 
        })

        $('#id_urlquery').bind('keypress', function(eventObject) {
            var key = eventObject.charCode ? eventObject.charCode : eventObject.keyCode ? eventObject.keyCode : 0;
            var target = eventObject.target.tagName.toLowerCase();
            if (key === 13 && target === 'input') {
                eventObject.preventDefault();
                sendCode(); 
                return false; 
            }
            return true; 
        })

        $('#id_urlquery').focus(function() {
            if ($(this).hasClass('hint')) {
                $(this).val('');
                $(this).removeClass('hint');
            }
        });
        $('#id_urlquery').blur(function() {
            if(!$(this).hasClass('hint') && ($(this).val() == '')) {
                $(this).val('urlquery');
                $(this).addClass('hint');
            }
        });
        $('#id_urlquery').blur();
    }
    
    //Setup Tabs
    function setupTabs(){
        
        $('.editor_output .console a').click(function(){
            showTab('console');
            return false;
        });
        $('.editor_output .data a').click(function(){
            showTab('data');
            return false;
        })
        $('.editor_output .sources a').click(function(){
            showTab('sources');
            return false;
        })
        $('.editor_output .chat a').click(function(){
            showTab('chat');
            return false;
        })

        //show default tab
        showTab('console'); 
    }
    
    // show the bottom grey sliding up message
    function showFeedbackMessage(sMessage){
       $('#feedback_messages').html(sMessage)
       $('#feedback_messages').slideToggle(200);
       setTimeout('$("#feedback_messages").slideToggle();', 2500);
    }


    conn.onopen = function(code){
        sChatTabMessage = 'Chat'; 
        $('.editor_output div.tabs li.chat a').html(sChatTabMessage);

        if (conn.readyState == conn.READY_STATE_OPEN)
            mreadystate = 'Ready'; 
        else
            mreadystate = 'readystate=' + conn.readyState;
        writeToChat('Connection opened: ' + mreadystate); 
        bConnected = true; 

        // send the username and guid of this connection to twisted so it knows who's logged on
        data = { "command":'connection_open', 
                 "guid":guid, 
                 "username":username, 
                 "userrealname":userrealname, 
                 "language":scraperlanguage, 
                 "scrapername":short_name, 
                 "isstaff":isstaff };
        send(data);
    }

    conn.onclose = function(code){
        if (code == Orbited.Statuses.ServerClosedConnection)
            mcode = 'ServerClosedConnection'; 
        else if (code == Orbited.Errors.ConnectionTimeout)
            mcode = 'ConnectionTimeout'; 
        else  
            // http://orbited.org/wiki/TCPSocket documents: 
            //    Orbited.Errors.InvalidHandshake = 102
            //    Orbited.Errors.UserConnectionReset = 103
            //    Orbited.Errors.Unauthorized = 106
            //    Orbited.Errors.RemoteConnectionFailed = 108
            //    Orbited.Statuses.SocketControlKilled = 301
            mcode = 'code=' + code;

        writeToChat('Connection closed: ' + mcode); 
        bConnected = false; 

        // couldn't find a way to make a reconnect button work!
            // the bSuppressDisconnectionMessages technique doesn't seem to work (unload is not invoked), so delay message  in the hope that window will close first
        if (!bSuppressDisconnectionMessages)
            setTimeout(function() {
                writeToChat('<b>You will need to reload the page to reconnect</b>');  
                writeToConsole("Connection to execution server lost, you will need to reload this page.", "exceptionnoesc"); 
                writeToConsole("(You can still save your work)", "exceptionnoesc"); }, 
                25); 


        $('.editor_controls #run').val('Unconnected');
        $('.editor_controls #run').unbind('click.run');
        $('.editor_controls #run').unbind('click.abort');
        $('#running_annimation').hide(); 

        sChatTabMessage = 'Disconnected'; 
        $('.editor_output div.tabs li.chat a').html(sChatTabMessage);
    }

    //read data back from twisted
    conn.onread = function(ldata) {
        buffer = buffer+ldata;
        while (true) {
            var linefeed = buffer.indexOf("\n"); 
            if (linefeed == -1)
                break; 
            sdata = buffer.substring(0, linefeed); 
            buffer = buffer.substring(linefeed+1); 
            sdata = sdata.replace(/[\s,]+$/g, '');  // trailing commas cannot be evaluated in IE
            if (sdata.length == 0)
                continue; 

            var jdata = undefined; 
            try {
                //writeToChat(cgiescape(sdata)); // for debug of what's coming out
                jdata = $.evalJSON(sdata);
            } catch(err) {
                alert("Malformed json: '''" + sdata + "'''"); 
            }

            if (jdata != undefined) {
                if ((jdata.message_type == 'chat') || (jdata.message_type == 'editorstatus'))
                    receivechatqueue.push(jdata); 
                else
                    receiverecordqueue.push(jdata); 

                // allow the user to clear the choked data if they want
                if ((jdata.message_type == 'executionstatus')  && (jdata.content == 'runfinished')) {
                        $('.editor_controls #run').val('Finishing');
                        $('.editor_controls #run').unbind('click.abort');
                        $('.editor_controls #run').bind('click.stopping', clearJunkFromQueue);
                }

                if (receiverecordqueue.length + receivechatqueue.length == 1)
                    window.setTimeout(function() { receiveRecordFromQueue(); }, 1);  // delay of 1ms makes it work better in FireFox (possibly so it doesn't take priority over the similar function calls in Orbited.js)

                // clear batched up data that's choking the system
                if ((jdata.message_type == 'executionstatus')  && (jdata.content == 'killrun'))
                    window.setTimeout(clearJunkFromQueue, 1); 
            }
        }
    }

    function clearJunkFromQueue() {
        var lreceiverecordqueue = [ ]; 
        for (var i = 0; i < receiverecordqueue.length; i++) {
            jdata = receiverecordqueue[i]; 
            if ((jdata.message_type != "data") && (jdata.message_type != "console"))
                lreceiverecordqueue.push(jdata); 
        }
        if (receiverecordqueue.length != lreceiverecordqueue.length) {
            message = "Clearing " + (receiverecordqueue.length - lreceiverecordqueue.length) + " records from receiverqueue, leaving: " + lreceiverecordqueue.length; 
            writeToConsole(message); 
            receiverecordqueue = lreceiverecordqueue; 
        }
    }

    // run our own queue not in the timeout system (letting chat messages get to the front)
    function receiveRecordFromQueue() {
        var jdata = undefined; 
        if (receivechatqueue.length > 0)
            jdata = receivechatqueue.shift(); 
        else if (receiverecordqueue.length > 0) 
            jdata = receiverecordqueue.shift(); 

        if (jdata != undefined) {
            receiveRecord(jdata);
            if (receiverecordqueue.length + receivechatqueue.length >= 1)
                window.setTimeout(function() { receiveRecordFromQueue(); }, 1); 
        }
    }

    //read data back from twisted
    function receiveRecord(data) {
          if (data.message_type == "console") {
              writeRunOutput(data.content);     // able to divert text to the preview iframe
          } else if (data.message_type == "sources") {
              writeToSources(data.url, data.bytes, data.failedmessage, data.cached, data.cacheid)
          } else if (data.message_type == "editorstatus") {
              recordEditorStatus(data); 
          } else if (data.message_type == "chat") {
              writeToChat(cgiescape(data.content))
          } else if (data.message_type == "saved") {
              writeToChat(cgiescape(data.content))
          } else if (data.message_type == "othersaved") {
              reloadScraper();
              writeToChat("OOO: " + cgiescape(data.content))
          } else if (data.message_type == "data") {
              writeToData(data.content);
          } else if (data.message_type == "exception") {
              writeExceptionDump(data.exceptiondescription, data.stackdump, data.blockedurl, data.blockedurlquoted); 
          } else if (data.message_type == "executionstatus") {
              if (data.content == "startingrun")
                startingrun(data.runID);
              else if (data.content == "runcompleted")
                writeToConsole("Finished: " + data.elapsed_seconds + " seconds elapsed, " + data.CPU_seconds + " CPU seconds used"); 
              else if (data.content == "killsignal")
                writeToConsole(data.message); 
              else if (data.content == "runfinished")
                endingrun(data.content); 
              else 
                writeToConsole(data.content); 

          } else {
              writeToConsole(data.content, data.message_type); 
          }
      }        

    function sendChat() 
    {
        data = {"command":'chat', "guid":guid, "username":username, "text":$('#chat_line').val()};
        send(data); 
        $('#chat_line').val(''); 
    }

    //send a message to the server
    function send(json_data) {
        try {
            conn.send($.toJSON(json_data));  
        } catch(err) {
            alert("Send error: " + err); 
        }
    }

    //send a 'kill' message
    function sendKill() {
        data = {"command" : 'kill'};
        send(data);
    }

    //send code request run
    function sendCode() {
        // protect not-ready case
        if (conn.readyState != conn.READY_STATE_OPEN) { 
            alert("Not ready, readyState=" + conn.readyState); 
            return; 
        }

    
        //send the data
        data = {
            "command" : "run",
            "guid" : guid,
            "username" : username, 
            "userrealname" : userrealname, 
            "language":scraperlanguage, 
            "scraper-name":short_name,
            "code" : codeeditor.getCode(),
            "urlquery" : ($('#id_urlquery').hasClass('hint') ? '' : $('#id_urlquery').val())
        }
        send(data)

        // the rest of the activity happens in startingrun when we get the startingrun message come back from twisted
        // means we can have simultaneous running for staff overview

        // new auto-save every time 
        if (guid && $('#id_autosavecheck').attr('checked') && pageIsDirty)
            saveScraper(); 
    }

    function updateEditorStatus() { 
        // Construct a message that reflects the situation for now.  
        // Later on add in options to allow auto-reload and ability to find the names of those who are watching
        var message = "";
        var nwatchers = loggedineditors.length + nanonymouseditors; 
        if (username)
        {
            if (editinguser == username)
            {
                if (nwatchers > 1)
                    message += (nwatchers-1) + " watching"; 
            }
            else
            {
                message += editinguser + " is editing; "; 
                message += "you"; 
                if (nwatchers > 2)
                    message += " (+ " + (nwatchers-2) + " others)"; 
                message += " are watching"; 
            }
        }
        else
        {
            if (editinguser)
                message += editinguser + " is editing; "; 
            var owatchers = nwatchers - 1 - (editinguser ? 1 : 0); 
            if (owatchers > 0)
                message += owatchers + " others watching"; 
        }
        $("#editorstatus").html(message); 
    }

    function recordEditorStatus(data) { 
        earliesteditor = data.earliesteditor; 
        editinguser = data.editinguser; 
        bcansave = data.cansave; 
        loggedineditors = data.loggedineditors; 
        nanonymouseditors = data.nanonymouseditors; 

        writeToChat(cgiescape("editorstatusdata: " + $.toJSON(data))); 
        if (data.message)
            writeToChat(cgiescape(data.message)); 

        window.setTimeout(function() { updateEditorStatus(); }, 100);  
    }

    function startingrun(lrunID) {
        //show the output area
        resizeControls('up');
        
        document.title = document.title + ' *'

        $('#running_annimation').show();
        runID = lrunID; 

        //clear the tabs
        clearOutput();
        writeToConsole('Starting run ... '); 

        //unbind run button
        $('.editor_controls #run').unbind('click.run')
        $('.editor_controls #run').addClass('running').val('Stop');

        //bind abort button
        $('.editor_controls #run').bind('click.abort', function() {
            sendKill();
            $('.editor_controls #run').val('Stopping');
            $('.editor_controls #run').unbind('click.abort');
            $('.editor_controls #run').bind('click.stopping', clearJunkFromQueue);
        });
    }
    
    function endingrun(content) {
        $('.editor_controls #run').removeClass('running').val('run');
        $('.editor_controls #run').unbind('click.abort');
        $('.editor_controls #run').unbind('click.stopping');
        $('.editor_controls #run').bind('click.run', sendCode);
        writeToConsole(content)

        //change title
        document.title = document.title.replace('*', '')
    
        //hide annimation
        $('#running_annimation').hide();
        runID = ''; 

        // suppress any more activity to the preview frame
        if (activepreviewiframe != undefined) {
            activepreviewiframe.document.close(); 
            activepreviewiframe = undefined; 
        }
    }


    function viewDiff(){
        $.ajax({
            type: 'POST',
            url: '/editor/diff/' + short_name,
            data: ({
                code: codeeditor.getCode()
                }),
            dataType: "html",
            success: function(diff) {
                $.modal('<pre class="popupoutput">'+cgiescape(diff)+'</pre>', {
                        overlayClose: true 
                       });
            }
        });
    }

    function clearOutput(){
        $('#output_console div').html('');    
        $('#output_sources div').html('');    
        $('#output_data table').html('');                    
        $('.editor_output div.tabs li.console').removeClass('new');
        $('.editor_output div.tabs li.data').removeClass('new');        
        $('.editor_output div.tabs li.sources').removeClass('new');        
    }

    function reloadScraper(){
        if (shortNameIsSet() == false) {
            alert("Cannot reload draft scraper");
            return; 
        }


        // send current code up to the server and get a copy of new code
        var newcode = $.ajax({
                         url: '/editor/raw/' + short_name, 
                         async: false, 
                         type: 'POST', 
                         data: ({oldcode: codeeditor.getCode()}) 
                       }).responseText; 

        // extract the (changed) select range information from the header of return data
        var selrangedelimeter = ":::sElEcT rAnGe:::"; 
        var iselrangedelimeter = newcode.indexOf(selrangedelimeter); 
        var selrange = [0,0,0,0];
        if (iselrangedelimeter != -1) {
            var selrange = newcode.substring(0, iselrangedelimeter); 
            newcode = newcode.substring(iselrangedelimeter + selrangedelimeter.length); 
            selrange = $.evalJSON(selrange); 
        }

        codeeditor.setCode(newcode); // see setupTutorial() for way to leave control-Z in place
        codeeditor.focus(); 
        setPageIsDirty(false); 

        // make the selection
        if (!((selrange[2] == 0) && (selrange[3] == 0))){
            linehandlestart = codeeditor.nthLine(selrange[0] + 1); 
            linehandleend = codeeditor.nthLine(selrange[2] + 1); 
            codeeditor.selectLines(linehandlestart, selrange[1], linehandleend, selrange[3]); 
        }

        showFeedbackMessage("This scraper has been reloaded.");
    }; 


    function run_abort() {
            runRequest = runScraper();
            $('.editor_controls #run').unbind('click.run');
            $('.editor_controls #run').addClass('running').val('Stop');
            $('.editor_controls #run').bind('click.abort', function() {
                sendKill();
                $('.editor_controls #run').removeClass('running').val('run');
                $('.editor_controls #run').unbind('click.abort');
                writeToConsole('Run Aborted'); 
                $('.editor_controls #run').bind('click.run', run_abort);
                
                //hide annimation
                $('#running_annimation').hide();
                
                //change title
                document.title = document.title.replace(' *', '');
            });
            
        }
    
    
    //Setup toolbar
    function setupToolbar(){

        // actually the save button
        $('#btnCommitPopup').live('click', function (){
            saveScraper();  
            return false;
        });
        
        //diff button (hidden)
         $('.editor_controls #diff').click(function() {
                viewDiff(); 
                return false; 
            }
        ); 

        //reload button (hidden)
         $('.editor_controls #reload').click(function() {
                reloadScraper(); 
                return false; 
            }
        );

        //close editor link
        $('#aCloseEditor, #aCloseEditor1, .page_tabs a').click(
            function (){
                if (pageIsDirty && !confirm("You have unsaved changes, close the editor anyway?"))
                    return false; 
                bSuppressDisconnectionMessages = true; 
                send({"command":'loseconnection'}) 
                // if (conn)  conn.close();  
                return true;
            }
        );

        $(window).unload( function () { 
            bSuppressDisconnectionMessages = true; 
            writeToConsole('window unload'); 
            if (conn)  conn.close();  
        });  


        if (wiki_type == 'view')
            $('.editor_controls #preview').bind('click.run', popupPreview);
        else
            $('.editor_controls #preview').hide();

        // available only for php cases
        $('#togglelanguage').bind('click', function () 
        { 
            if (!$(this).hasClass('htmltoggled')) {
                $(this).html('toggle PHP');
                $(this).addClass('htmltoggled');
                codeeditor.setParser(parserName["html"], parserConfig["php"]); 
            } else {
                $(this).html('toggle HTML');
                $(this).removeClass('htmltoggled');
                codeeditor.setParser(parserName["php"], parserConfig["php"]); 
            }
        }); 

        if (scraperlanguage == 'html')
            $('.editor_controls #run').hide();
        else
            $('.editor_controls #run').bind('click.run', sendCode);
    }

    function popupPreview() {
        var viewurl = viewrunurl; 
        var urlquery = ($('#id_urlquery').hasClass('hint') ? '' : $('#id_urlquery').val()); 
        var viewurl = viewrunurl; 
        var previewmessage = ''; 
        if (urlquery.length != 0) {
            if (urlquery.match(/^[\w%_.;&~+=\-]+$/g)) 
                viewurl = viewurl + '?' + urlquery; 
            else
                previewmessage = ' [' + urlquery + '] is an invalid query string'; 
        }

        previewscreen = '<h3>View preview <small><a href="'+viewurl+'" target="_blank">'+viewurl+'</a>'+previewmessage+'</small></h3>'; 
        isrc = ""; // isrc = viewurl; (would allow direct inclusion from saved version)
            // force the preview iframe to fill most of what it should.  needs more work
        previewscreen += '<iframe id="previewiframe" width="100%" height="'+($(window).height()*8/10-50)+'px" src="'+isrc+'"></iframe>'; 

        $.modal(previewscreen, { 
            overlayClose: true,
            containerCss: { borderColor:"#fff", height:"80%", padding:0, width:"90%" }, 
            overlayCss: { cursor:"auto" }, 
            onShow: function(d) {
                ifrm = document.getElementById('previewiframe');
                activepreviewiframe = (ifrm.contentWindow ? ifrm.contentWindow : (ifrm.contentDocument.document ? ifrm.contentDocument.document : ifrm.contentDocument));
                activepreviewiframe.document.open(); 
                sendCode(); // trigger the running once we're ready for the output
            }
        }); 
    }

    //Save
    function saveScraper(){
        var bSuccess = false;

        //if saving then check if the title is set (must be if guid is set)
        if(shortNameIsSet() == false){
            var sResult = jQuery.trim(prompt('Please enter a title for your scraper'));
            if (sResult != false && sResult != '' && sResult != 'Untitled') {
                $('#id_title').val(sResult);
                aPageTitle = document.title.split('|')
                document.title = sResult + ' | ' + aPageTitle[1]
                bSuccess = true;
            }
        }else{
            bSuccess = true;
        }
        if(bSuccess == true){      
            $.ajax({
              type : 'POST',
              contentType : "application/json",
              URL : window.location.pathname,

              data: ({
                title : $('#id_title').val(),
                commit_message: "cccommit",
                sourcescraper: $('#sourcescraper').val(),
                wiki_type: wiki_type,
                code : codeeditor.getCode(),
                earliesteditor : earliesteditor, 
                action : 'commit'
                }),

              dataType: "html",
              success: function(response){
                    res = $.evalJSON(response);

                    //failed
                    if (res.status == 'Failed'){
                        alert("Save failed error message.  Shouldn't happen"); 

                    //success    
                    }else{
                        //pageTracker._trackPageview('/scraper_committed_goal');  		

                        // 'A temporary version of your scraper has been saved. To save it permanently you need to log in'
                        if (res.draft == 'True') {
                            $('#divDraftSavedWarning').show();
                        }

                        // server returned a different URL for the new scraper that has been created.  Now go to it (and reload)
                        if (res.url && window.location.pathname != res.url) {
                            window.location = res.url;
                        };

                        // orginary save case.  show the slider up that it has been saved
                        if (res.draft != 'True') {
                            showFeedbackMessage("Your code has been saved.");
                            if (bConnected){
                                send({"command":'saved'}); 
                            }
                        }
                        setPageIsDirty(false); 
                    }
                },

            error: function(response){
                alert('Sorry, something went wrong, please try copying your code and then reloading the page');
                document.write(response.responseText); // Uncomment to get the actual error page
              }
            });
        }
    }

    function cgiescape(text) {
        if(text){
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;');
        }else{
            return "";
        }
    }

    
    function setupResizeEvents(){
        
        //window
        $(window).resize(onWindowResize);
        
        //editor
        $("#codeeditordiv").resizable({
                         handles: 's',   
                         autoHide: false, 
                         start: function(event, ui) 
                             {
                                 var maxheight = $("#codeeditordiv").height() + $(window).height() - $("#outputeditordiv").position().top;

                                 $("#codeeditordiv").resizable('option', 'maxHeight', maxheight);

                                 //cover iframe
                                 var oFrameMask = $('<div id="framemask"></div>');
                                 oFrameMask.css({
                                     position: 'absolute',
                                     top: 0,
                                     left:0,
                                     background:'none',
                                     zindex: 200,
                                     width: '100%',
                                     height: '100%'
                                 })
                                 $(".editor_code").append(oFrameMask)
                             },
                         stop: function(event, ui)  { 
                                     resizeCodeEditor(); 
                                     $('#framemask').remove();
                                 }
                             }); 

           // bind the double-click (causes problems with the jquery interface as it doesn't notice the mouse exiting the frame
           // $(".ui-resizable-s").bind("dblclick", resizeControls);
    }

    function shortNameIsSet(){
        var sTitle = jQuery.trim($('#id_title').val());
        return sTitle != 'Untitled' && sTitle != '' && sTitle != undefined && sTitle != false;
    }

    //Hide popup
    function hidePopup() {

        // Hide popups
        $('#popups div.popup_item').each(function(i) {
            $(this).fadeOut("fast")
        });

        //hide overlay
        $('#popups #overlay').fadeOut("fast")
        popupStatus = 0;
                
        // set focus to the code editor so we can carry on typing
        codeeditor.focus(); 
    }

    function writeExceptionDump(exceptiondescription, stackdump, blockedurl, blockedurlquoted) {
        if (stackdump) {
            for (var i = 0; i < stackdump.length; i++) {
                var stackentry = stackdump[i]; 
                sMessage = (stackentry.file != undefined ? (stackentry.file == "<string>" ? stackentry.linetext : stackentry.file) : ""); 
                if (stackentry.furtherlinetext != undefined)
                    sMessage += " -- " + stackentry.furtherlinetext; 
                linenumber = (stackentry.file == "<string>" ? stackentry.linenumber : undefined); 
                writeToConsole(sMessage, 'exceptiondump', linenumber); 
                if (stackentry.duplicates > 1)
                    writeToConsole("  + " + stackentry.duplicates + " duplicates", 'exceptionnoesc'); 
            }
        }

        if (blockedurl) {
            sMessage = "The link " + blockedurl.substring(0,50) + " has been blocked. "; 
            sMessage += "Click <a href=\"/whitelist/?url=" + blockedurlquoted + "\" target=\"_blank\">here</a> for details."; 
            writeToConsole(sMessage, 'exceptionnoesc'); 
        }
        else
            writeToConsole(exceptiondescription, 'exceptiondump'); 
    }

    function writeRunOutput(sMessage) {
        writeToConsole(sMessage, 'console'); 
        if ((activepreviewiframe != undefined) && (activepreviewiframe.document != undefined))
            activepreviewiframe.document.write(sMessage); 
    }

    function showTextPopup(sLongMessage) {
        $.modal('<pre class="popupoutput">'+cgiescape(sLongMessage)+'</pre>', 
                {overlayClose: true, 
                 containerCss:{ borderColor:"#fff", height:"80%", padding:0, width:"90%", background:"#000", color:"#3cef3b" }, 
                 overlayCss: { cursor:"auto" }
                });
    }

    //Write to console/data/sources
    function writeToConsole(sMessage, sMessageType, iLine) {

        // if an exception set the class accordingly
        var sShortClassName = '';
        var sLongClassName = 'message_expander';
        var sExpand = '...more'

        var sLongMessage = undefined; 
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

        if(sLongMessage != undefined) {
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
        if ($('#output_console div.output_content').children().size() >= outputMaxItems) {
            $('#output_console div.output_content').children(':first').remove();
        }

        //append to console
        $('#output_console div.output_content').append(oConsoleItem);
        $('.editor_output div.tabs li.console').addClass('new');

        setTabScrollPosition('console', 'bottom'); 
    };


    function writeToSources(sUrl, bytes, failedmessage, cached, cacheid) {

        //remove items if over max
        if ($('#output_sources div.output_content').children().size() >= outputMaxItems) {
            $('#output_sources div.output_content').children(':first').remove();
        }

        //append to sources tab
        if (cacheid != undefined)
            malink = 'class="cached" href="/cachedscrape/' + cacheid + '"'; 
        else
            malink = 'href="' + sUrl + '"'; 
        alink = '<a ' + malink + ' target="_new">' + sUrl.substring(0, 100) + '</a> '; 
        if ((failedmessage != undefined) && (failedmessage != ''))
            smessage = failedmessage + alink; 
        else
            smessage = bytes + ' bytes loaded ' + (cached == 'True' ? '(from cache) ' : '') + alink; 

        $('#output_sources div.output_content').append('<span class="output_item">' + smessage + '</span>')
        $('.editor_output div.tabs li.sources').addClass('new');
        setTabScrollPosition('sources', 'bottom'); 
    }

    function writeToData(aRowData) {
        var oRow = $('<tr></tr>');

        $.each(aRowData, function(i){
            var oCell = $('<td></td>');
            oCell.html(cgiescape(aRowData[i]));
            oRow.append(oCell);
        })

        if ($('#output_data table.output_content tbody').children().size() >= outputMaxItems) {
            $('#output_data table.output_content tbody').children(':first').remove();
        }
        
        $('#output_data table.output_content').append(oRow);  // oddly, append doesn't work if we add tbody into this selection

        setTabScrollPosition('data', 'bottom'); 

        $('.editor_output div.tabs li.data').addClass('new');
    }

    function writeToChat(seMessage) {
        var oRow = $('<tr></tr>');
        var oCell = $('<td></td>');
        oCell.html(seMessage);
        oRow.append(oCell);
        

        if ($('#output_chat table.output_content tbody').children().size() >= outputMaxItems) {
            $('#output_chat table.output_content tbody').children(':first').remove();
        }

        $('#output_chat table.output_content').append(oRow);

        setTabScrollPosition('chat', 'bottom'); 

        $('.editor_output div.tabs li.chat').addClass('new');
    }

    // some are implemented with tables, and some with span rows.  
    function setTabScrollPosition(sTab, command) {
        divtab = '#output_' + sTab; 
        contenttab = '#output_' + sTab; 

        if ((sTab == 'console') || (sTab == 'sources')) {
            divtab = '#output_' + sTab + ' div';
            contenttab = '#output_' + sTab + ' .output_content';
        }

        if (command == 'hide')
            scrollPositions[sTab] = $(divtab).scrollTop();
        else {
            if (command == 'bottom')
                scrollPositions[sTab] = $(contenttab).height()+$(divtab)[0].scrollHeight; 
            $(divtab).animate({ scrollTop: scrollPositions[sTab] }, 0);
        }
    }


    //show tab
    function showTab(sTab){
        setTabScrollPosition(sTabCurrent, 'hide'); 
        $('.editor_output .info').children().hide();
        $('.editor_output .controls').children().hide();        
        
        $('#output_' + sTab).show();
        $('#controls_' + sTab).show();
        sTabCurrent = sTab; 

        $('.editor_output div.tabs ul').children().removeClass('selected');
        $('.editor_output div.tabs li.' + sTab).addClass('selected');
        $('.editor_output div.tabs li.' + sTab).removeClass('new');
        setTabScrollPosition(sTab, 'show'); 
    }
    

    //resize code editor
   function resizeCodeEditor(){
      if (codemirroriframe){
          //resize the iFrame inside the editor wrapping div
          codemirroriframe.height = (($("#codeeditordiv").height() + codemirroriframeheightdiff) + 'px');
          codemirroriframe.width = (($("#codeeditordiv").width() + codemirroriframewidthdiff) + 'px');

          //resize the output area so the console scrolls correclty
          iWindowHeight = $(window).height();
          iEditorHeight = $("#codeeditordiv").height();
          iControlsHeight = $('.editor_controls').height()
          iCodeEditorTop = parseInt($("#codeeditordiv").position().top);
          iOutputEditorTabs = $('#outputeditordiv .tabs').height()
          iOutputEditorDiv = iWindowHeight - (iEditorHeight + iControlsHeight + iCodeEditorTop) - 30; 
          $("#outputeditordiv").height(iOutputEditorDiv + 'px');   
          //$("#outputeditordiv .info").height($("#outputeditordiv").height() - parseInt($("#outputeditordiv .info").position().top) + 'px');
          $("#outputeditordiv .info").height((iOutputEditorDiv - iOutputEditorTabs) + 'px');
          //iOutputEditorTabs
      }
    };
    

    //click bar to resize
    function resizeControls(sDirection) {
    
        if (sDirection == 'first')
            previouscodeeditorheight = $(window).height() * 3/5; 
        else if (sDirection != 'up' && sDirection != 'down')
            sDirection = 'none';

        //work out which way to go
        var maxheight = $("#codeeditordiv").height() + $(window).height() - ($("#outputeditordiv").position().top + 5); 
        if (($("#codeeditordiv").height() + 5 <= maxheight) && (sDirection == 'none' || sDirection == 'down')) 
        {
            previouscodeeditorheight = $("#codeeditordiv").height();
            $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor); 
        } 
        else if ((sDirection == 'first') || (sDirection == 'none') || ((sDirection == 'up') && ($("#codeeditordiv").height() + 5 >= maxheight)))
            $("#codeeditordiv").animate({ height: Math.min(previouscodeeditorheight, maxheight - 5) }, 100, "swing", resizeCodeEditor); 
    }

    function onWindowResize() {
        var maxheight = $("#codeeditordiv").height() + $(window).height() - $("#outputeditordiv").position().top; 
        if (maxheight < $("#codeeditordiv").height()){
            $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor);
        }
        resizeCodeEditor();
    }

    //add hotkey - this is a hack to convince codemirror (which is in an iframe) / jquery to play nice with each other
    //which means we have to do some seemingly random binds/unbinds
    function addHotkey(sKeyCombination, oFunction){

        $(document).bind('keydown', sKeyCombination, function(){return false;});
        $(codeeditor.win.document).unbind('keydown', sKeyCombination);
        $(codeeditor.win.document).bind('keydown', sKeyCombination,
            function(oEvent){
                oFunction();

                return false;                            
            }
        );
    }
   
   
});
