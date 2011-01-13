$(document).ready(function() {

    // editor window dimensions
    var editor_id = 'id_code';
    var codeeditor = undefined;
    var codemirroriframe = undefined; // the actual iframe of codemirror that needs resizing (also signifies the frame has been built)
    var codeeditorbackgroundimage = 'none'; 
    var codemirroriframeheightdiff = 0; // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var codemirroriframewidthdiff = 0;  // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var previouscodeeditorheight = 0; //$("#codeeditordiv").height() * 3/5;    // saved for the double-clicking on the drag bar

    // variable transmitted through the html
    var short_name      = $('#short_name').val();
    var guid            = $('#scraper_guid').val();
    var username        = $('#username').val(); 
    var userrealname    = $('#userrealname').val(); 
    var isstaff         = $('#isstaff').val(); 
    var scraperlanguage = $('#scraperlanguage').val(); 
    var run_type        = $('#code_running_mode').val();
    var codemirror_url  = $('#codemirror_url').val();
    var wiki_type       = $('#id_wiki_type').val(); 
    var rev             = $('#originalrev').val(); 

    // runtime information
    var activepreviewiframe = undefined; // used for spooling running console data into the preview popup
    var conn = undefined; // Orbited connection
    var bConnected  = false; 
    var bSuppressDisconnectionMessages = false; 
    var buffer = "";
    var selectedTab = 'console';
    var outputMaxItems = 400;
    var sTabCurrent = ''; 
    var sChatTabMessage = 'Chat'; 
    var scrollPositions = { 'console':0, 'data':0, 'sources':0, 'chat':0 }; 
    var receiverecordqueue = [ ]; 
    var receivechatqueue = [ ]; 
    var runID = ''; 
    var uml = ''; 

    // information handling who else is watching and editing during this session
    var editingusername = "";  // primary editor
    var loggedineditors = [ ]; // list of who else is here and their windows open
    var iselectednexteditor = 1; 
    var nanonymouseditors = 0; // number of anonymous editors
    var chatname = ""          // special in case of Anonymous users (yes, this unnecessarily gets set every time we call recordEditorStatus)
    var chatpeopletimes = { }; // last time each person made a chat message

    // these actually get set by the server
    var servernowtime = new Date(); 
    var earliesteditor = servernowtime; 
    var lasttouchedtime = undefined; 

    var parsers = Array();
    var stylesheets = Array();
    var indentUnits = Array();
    var parserConfig = Array();
    var parserName = Array();
    var codemirroroptions = undefined; 
    var pageIsDirty = false;
    var atsavedundo = 0; // recorded at start of save operation
    var savedundo = 0; 
    var lastundo = 0; 

    var cachehidlookup = { }; // this itself is a cache of a cache
    
    var chainpatches = [ ]; 
    var chainpatchnumber = 0; // counts them going out
    var lasttypetime = new Date(); 

    $.ajaxSetup({timeout: 10000});

    setupCodeEditor();
    setupMenu();
    setupTabs();
    setupToolbar();
    setupResizeEvents();
    setupOrbited();


    function CM_cleanText(text)  { return text.replace(/\u00a0/g, " ").replace(/\u200b/g, ""); }
    function CM_isBR(node)  { var nn = node.nodeName; return nn == "BR" || nn == "br"; }
    function CM_nodeText(node)  { return node.textContent || node.innerText || node.nodeValue || ""; }
    function CM_lineNumber(node)
    {
        if (node == null)
            return 1; 
        if (node.parentNode != codeeditor.win.document.body)
            return -1; 
        var num = 1;
        while (node)
        {
            num++; 
            node = node.previousSibling; 
            while (node && !CM_isBR(node))
                 node = node.previousSibling; 
        }
        return num;
    }

    function CM_newLines(from, to) 
    {
        var lines = [ ]
        var text = [ ];
        for (var cur = (from ? from.nextSibling : codeeditor.editor.container.firstChild); cur != to; cur = cur.nextSibling)
        {
            if (CM_isBR(cur))
            {
                lines.push(CM_cleanText(text.join(""))); 
                text = [ ]
            }
            else
                text.push(CM_nodeText(cur)); 
        }
        lines.push(CM_cleanText(text.join(""))); 
        return lines; 
    }

    // keep delivery load of chain patches down and remove excess typing signals
    function sendChainPatches()
    {
        if (chainpatches.length > 0)
            sendjson(chainpatches.shift()); 

        // clear out the ones that are pure typing messages sent in non-broadcast mode
        while ((chainpatches.length > 0) && (chainpatches[0].insertlinenumber == undefined))
            chainpatches.shift(); 

        if (chainpatches.length > 0)
            setTimeout(sendChainPatches, 2); 
    }


    function ChangeInEditor(changetype) 
    {
        lasttypetime = new Date(); 
        var historysize = codeeditor.historySize(); // should have (+ historysize.shiftedoffstack)
        var automode = $('select#automode option:selected').val(); 

        if (changetype == "saved")
            savedundo = atsavedundo;    // (+historysize.shiftedoffstack)
        if (changetype == "reload")
            savedundo = historysize.undo;   // (+historysize.shiftedoffstack) 

        if (historysize.undo + historysize.redo < savedundo)
            savedundo = -1; 
        var lpageIsDirty = (historysize.undo != savedundo); 

        if (pageIsDirty != lpageIsDirty)
        {
            pageIsDirty = lpageIsDirty; 
            $('#aCloseEditor1').css("font-style", ((pageIsDirty && guid) ? "italic" : "normal")); 

        // we can only enter broadcast mode from a clean file
        // in the future we could maintain a stack of patches here and upload them when the broadcast mode is entered
        // so that they apply retrospectively.  
        // also we can do the saving through twister and bank a stack of patches there
        // that will be applied when someone else opens a window
            if (pageIsDirty && (automode != 'autotype'))
                $('select#automode #id_autotype').attr('disabled', true); 
            else if (!pageIsDirty && !$('select#automode #id_autosave').attr('disabled'))
                $('select#automode #id_autotype').attr('disabled', false); 
        }

        if (changetype != 'edit')
            return; 

    // to do: arrange for there to be only one autotype/broadcast window for a user
    // if the set it for one clients, then any other client that is in this mode gets 
    // reverted back to editing.  So it's clear which window is actually active and sending signals

    // also may want a facility for a watching user to be able to select an area in his window
    // and make it appear selected for the broadcast user
        if (automode == 'autotype')
        {
            // send any edits up the line (first to the chat page to show we can decode it)
            var historystack = codeeditor.editor.history.history; 
            var redohistorystack = codeeditor.editor.history.redoHistory; 
            var rdhL = redohistorystack.length - 1; 
            while (lastundo != historystack.length)
            {
                var chains; 
                if (lastundo < historystack.length)
                    chains = historystack[lastundo++]; 
                else if (rdhL >= 0)
                {
                    chains = redohistorystack[rdhL--]; 
                    lastundo--; 
                }
                else
                    break; 
    
                var lchainpatches = [ ]; 
                for (var i = 0; i < chains.length; i++)
                {
                    var chain = chains[i]; 
                    var chainpatch = { command:'typing', insertlinenumber:CM_lineNumber(chain[0].from), deletions:[ ], insertions:[ ], "chainpatchnumber":(chainpatchnumber++), "rev":rev }
                    for (var k = 0; k < chain.length; k++)
                        chainpatch["deletions"].push(chain[k].text); 
    
                    var lines = CM_newLines(chain[0].from, chain[chain.length - 1].to); 
                    for (var j = 0; j < lines.length; j++)
                        chainpatch["insertions"].push(lines[j]); 
                    lchainpatches.push(chainpatch); 
                }

                    // arrange for the chainpatches list (which is reversed) to add the upper ones first, because the line numbering 
                    // is detected against the final version after this chainpatch group has been done, so upper ones have occurred
                lchainpatches.sort(function(a,b) {return b["insertlinenumber"] - a["insertlinenumber"]});  
                while (lchainpatches.length)
                    chainpatches.push(lchainpatches.pop()); 
            }
        }

        else if ((automode == 'autosave') && bConnected)
            chainpatches.push({"command":'typing'}); 

        if (chainpatches.length > 0)
            sendChainPatches(); 
    }



    //setup code editor
    function setupCodeEditor(){
        parsers['python'] = ['../contrib/python/js/parsepython.js'];
        parsers['php'] = ['../contrib/php/js/tokenizephp.js', '../contrib/php/js/parsephp.js', '../contrib/php/js/parsephphtmlmixed.js' ];
        parsers['ruby'] = ['../../ruby-in-codemirror/js/tokenizeruby.js', '../../ruby-in-codemirror/js/parseruby.js'];
        //parsers['ruby'] = [ 'parsedummy.js'];   // in case Ruby parser needs disabling due to too many bugs
        parsers['html'] = ['parsexml.js', 'parsecss.js', 'tokenizejavascript.js', 'parsejavascript.js', 'parsehtmlmixed.js']; 

        stylesheets['python'] = [codemirror_url+'contrib/python/css/pythoncolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['php'] = [codemirror_url+'contrib/php/css/phpcolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['ruby'] = ['/media/ruby-in-codemirror/css/rubycolors.css', '/media/css/codemirrorcolours.css'];
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
        //parserName['ruby'] = 'DummyParser';  // for bugs
        parserName['html'] = 'HTMLMixedParser';

        // allow php to access HTML style parser
        parsers['php'] = parsers['html'].concat(parsers['php']);
        stylesheets['php'] = stylesheets['html'].concat(stylesheets['php']); 

        codemirroroptions = {
            parserfile: parsers[scraperlanguage],
            stylesheet: stylesheets[scraperlanguage],
            path: codemirror_url + "js/",
            domain: document.domain, 
            textWrapping: true,
            lineNumbers: true,
            indentUnit: indentUnits[scraperlanguage],
            readOnly: false, // cannot be changed once started up
            undoDepth: 200,  // defaults to 50.  wait till we get lostundo value
            undoDelay: 800, // 2 seconds  (default is 800)
            tabMode: "shift", 
            disableSpellcheck: true,
            autoMatchParens: true,
            width: '100%',
            parserConfig: parserConfig[scraperlanguage],
            enterMode: "flat", // default is "indent" (which I have found buggy),  also can be "keep"
            reindentOnLoad: false, 
            onChange: function ()  { ChangeInEditor("edit"); },  // (prob impossible to tell difference between actual typing and patch insertions from another window)
            //noScriptCaching: true, // essential when hacking the codemirror libraries

            // this is called once the codemirror window has finished initializing itself
            initCallback: function() {
                    codemirroriframe = codeeditor.frame // $("#id_code").next().children(":first"); (the object is now a HTMLIFrameElement so you have to set the height as an attribute rather than a function)
                    codemirroriframeheightdiff = codemirroriframe.height - $("#codeeditordiv").height(); 
                    codemirroriframewidthdiff = codemirroriframe.width - $("#codeeditordiv").width(); 
                    setupKeygrabs();
                    resizeControls('first');
                    setCodeeditorBackgroundImage(codeeditorbackgroundimage); // in case the signal got in first
                    ChangeInEditor("initialized"); 
                } 
          };

          codeeditor = CodeMirror.fromTextArea("id_code", codemirroroptions); 
    }


    function setupOrbited() 
    {
        TCPSocket = Orbited.TCPSocket;
        conn = new TCPSocket(); 
        conn.open('localhost', '9010'); 
        buffer = " "; 
        sChatTabMessage = 'Connecting...'; 
        $('.editor_output div.tabs li.chat a').html(sChatTabMessage);
    }


    function setCodeeditorBackgroundImage(lcodeeditorbackgroundimage)
    {
        codeeditorbackgroundimage = lcodeeditorbackgroundimage; 
        if (codemirroriframe != undefined) // also signifies the frame has been built
            codeeditor.win.document.body.style.backgroundImage = codeeditorbackgroundimage; 
    }

    //add hotkey - this is a hack to convince codemirror (which is in an iframe) / jquery to play nice with each other
    //which means we have to do some seemingly random binds/unbinds
    function addHotkey(sKeyCombination, oFunction)
    {
        $(document).bind('keydown', sKeyCombination, function(){return false;});
        $(codeeditor.win.document).unbind('keydown', sKeyCombination);
        $(codeeditor.win.document).bind('keydown', sKeyCombination,
            function(oEvent){
                oFunction();
                return false; 
            }
        );
    }

    function setupKeygrabs()
    {
        addHotkey('ctrl+s', saveScraper); 
        addHotkey('ctrl+r', sendCode);
        addHotkey('ctrl+p', popupPreview); 
        addHotkey('ctrl+h', popupHelp); 
    };

    function popupHelp()
    {
        var quickhelpurl = $('input#quickhelpurl').val(); 
        if (quickhelpurl)
        {
            // establish what word happens to be under the cursor here (and maybe even return the entire line for more context)
            var cursorpos = codeeditor.cursorPosition(true); 
            var cursorendpos = codeeditor.cursorPosition(false); 
            var quickhelpparams = { language:scraperlanguage, line:codeeditor.lineContent(cursorpos.line), character:cursorpos.character }; 
            if (cursorpos.line == cursorendpos.line)
                quickhelpparams["endcharacter"] = cursorendpos.character; 
            $.modal('<iframe width="100%" height="100%" src='+quickhelpurl+'?'+$.param(quickhelpparams)+'></iframe>', 
            {
                overlayClose: true,
                containerCss: { borderColor:"#fff", height:"80%", padding:0, width:"90%" }, 
                overlayCss: { cursor:"auto" }, 
            }); 
        }
        else
        {
            $('#popup_tutorials').modal(
            {
                 overlayClose: true, persist: true, 
                 containerCss:{ borderColor:"#0ff", height:"80%", padding:0, width:"90%" }, 
                 overlayCss: { cursor:"auto" }
            });
        };
    }

    //Setup Menu
    function setupMenu()
    {
        $('#menu_tutorials').click(popupHelp); 
        $('#chat_line').bind('keypress', function(eventObject) 
        {
            var key = (eventObject.charCode ? eventObject.charCode : eventObject.keyCode ? eventObject.keyCode : 0);
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

        $('#id_urlquery').bind('keypress', function(eventObject) 
        {
            var key = (eventObject.charCode ? eventObject.charCode : eventObject.keyCode ? eventObject.keyCode : 0);
            var target = eventObject.target.tagName.toLowerCase();
            if (key === 13 && target === 'input') 
            {
                eventObject.preventDefault();
                sendCode(); 
                return false; 
            }
            return true; 
        })

        // somehow this system fails if you do a browser back button to the editor
        $('#id_urlquery').focus(function() 
        {
            if ($(this).hasClass('hint')) {
                $(this).val('');
                $(this).removeClass('hint');
            }
        });
        $('#id_urlquery').blur(function() 
        {
            if(!$(this).hasClass('hint') && ($(this).val() == '')) {
                $(this).val('urlquery');
                $(this).addClass('hint');
            }
        });
        $('#id_urlquery').blur();

        $('select#automode').change(changeAutomode); 
        $('input#showautomode').change(showhideAutomodeSelector); 
    }
    
    //Setup Tabs
    function setupTabs()
    {
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
    

    conn.onopen = function(code)
    {
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
        sendjson(data);
    }

    conn.onclose = function(code)
    {
        if (code == Orbited.Statuses.ServerClosedConnection)
            mcode = 'ServerClosedConnection'; 
        else if (code == Orbited.Errors.ConnectionTimeout)
            mcode = 'ConnectionTimeout'; 
        else if (code == Orbited.Errors.InvalidHandshake)
            mcode = 'InvalidHandshake'; 
        else if (code == Orbited.Errors.UserConnectionReset)
            mcode = 'UserConnectionReset'; 
        else if (code == Orbited.Errors.Unauthorized)
            mcode = 'Unauthorized'; 
        else if (code == Orbited.Errors.RemoteConnectionFailed)
            mcode = 'RemoteConnectionFailed'; 
        else if (code == Orbited.Statuses.SocketControlKilled)
            mcode = 'SocketControlKilled'; 
        else
            mcode = 'code=' + code;

        writeToChat('Connection closed: ' + mcode); 
        bConnected = false; 

        // couldn't find a way to make a reconnect button work!
            // the bSuppressDisconnectionMessages technique doesn't seem to work (unload is not invoked), so delay message  in the hope that window will close first
        window.setTimeout(function() 
        {
            if (!bSuppressDisconnectionMessages)
            {
                writeToChat('<b>You will need to reload the page to reconnect</b>');  
                writeToConsole("Connection to execution server lost, you will need to reload this page.", "exceptionnoesc"); 
                writeToConsole("(You can still save your work)", "exceptionnoesc"); 
            }
        }, 250); 


        $('.editor_controls #run').val('Unconnected');
        $('.editor_controls #run').unbind('click.run');
        $('.editor_controls #run').unbind('click.abort');
        $('#running_annimation').hide(); 

        sChatTabMessage = 'Disconnected'; 
        $('.editor_output div.tabs li.chat a').html(sChatTabMessage);
    }

    //read data back from twisted
    conn.onread = function(ldata) 
    {
        buffer = buffer+ldata;
        while (true) 
        {
            var linefeed = buffer.indexOf("\n"); 
            if (linefeed == -1)
                break; 
            sdata = buffer.substring(0, linefeed); 
            buffer = buffer.substring(linefeed+1); 
            sdata = sdata.replace(/[\s,]+$/g, '');  // trailing commas cannot be evaluated in IE
            if (sdata.length == 0)
                continue; 

            var jdata; 
            try 
            {
                //writeToChat(cgiescape(sdata)); // for debug of what's coming out
                jdata = $.evalJSON(sdata);
            } 
            catch(err) 
            {
                alert("Malformed json: '''" + sdata + "'''"); 
                continue
            }

            if ((jdata.message_type == 'chat') || (jdata.message_type == 'editorstatus'))
                receivechatqueue.push(jdata); 
            else
                receiverecordqueue.push(jdata); 

            // allow the user to clear the choked data if they want
            if ((jdata.message_type == 'executionstatus')  && (jdata.content == 'runfinished')) 
            {
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

    function clearJunkFromQueue() 
    {
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
    function receiveRecordFromQueue() 
    {
        var jdata = undefined; 
        if (receivechatqueue.length > 0)
            jdata = receivechatqueue.shift(); 
        else if (receiverecordqueue.length > 0) 
            jdata = receiverecordqueue.shift(); 

        if (jdata != undefined) 
        {
            receiveRecord(jdata);
            if (receiverecordqueue.length + receivechatqueue.length >= 1)
                window.setTimeout(function() { receiveRecordFromQueue(); }, 1); 
        }
    }

    //read data back from twisted
    function receiveRecord(data) {
          if (data.nowtime)
             servernowtime = parseISOdate(data.nowtime); 

          if (data.message_type == "console") {
              writeRunOutput(data.content);     // able to divert text to the preview iframe
          } else if (data.message_type == "sources") {
              writeToSources(data.url, data.mimetype, data.bytes, data.failedmessage, data.cached, data.cacheid, data.ddiffer)
          } else if (data.message_type == "editorstatus") {
              recordEditorStatus(data); 
          } else if (data.message_type == "chat") {
              writeToChat(cgiescape(data.message), data.chatname); 
          } else if (data.message_type == "saved") {
              writeToChat("<i>saved</i>", data.chatname);  
          } else if (data.message_type == "othersaved") {
              reloadScraper();
              writeToChat("<i>saved in another window</i>", data.chatname);  
          } else if (data.message_type == "requestededitcontrol") {

// this should popup something if there has been no activity for a while with a count-down timer that eventually sets the editinguser down and
// self-demotes to autoload with the right value of iselectednexteditor selected
writeToChat("<b>requestededitcontrol: "+data.username+ " has requested edit control but you have last typed " + (new Date() - lasttypetime)/1000 + " seconds ago"); 

          } else if (data.message_type == "giveselrange") {
              //writeToChat("<b>selrange: "+data.chatname+" has made a select range: "+$.toJSON(data.selrange)+"</b>"); 
              makeSelection(data.selrange); // do it anyway
          } else if (data.message_type == "data") {
              writeToData(data.content);
          } else if (data.message_type == "exception") {
              writeExceptionDump(data.exceptiondescription, data.stackdump, data.blockedurl, data.blockedurlquoted); 
          } else if (data.message_type == "executionstatus") {
              if (data.content == "startingrun")
                startingrun(data.runID, data.uml, data.chatname);
              else if (data.content == "runcompleted")
                writeToConsole("Finished: " + data.elapsed_seconds + " seconds elapsed, " + data.CPU_seconds + " CPU seconds used"); 
              else if (data.content == "killsignal")
                writeToConsole(data.message); 
              else if (data.content == "runfinished")
                endingrun(data.content); 
              else 
                writeToConsole(data.content); 

          } else if (data.message_type == "httpresponseheader") {
              writeToConsole("Header:::", "httpresponseheader"); 
              writeToConsole(data.headerkey + ": " + data.headervalue, "httpresponseheader"); 
          } else if (data.message_type == "typing") {
              $('#lasttypedtimestamp').text(String(new Date())); 
          } else if (data.message_type == "othertyping") {
              $('#lasttypedtimestamp').text(String(new Date())); 
              if (data.insertlinenumber != undefined)
                  recordOtherTyping(data); 
          } else {
              writeToConsole(data.content, data.message_type); 
          }
      }

    function sendChat() 
    {
        lasttypetime = new Date(); 
        data = {"command":'chat', "guid":guid, "username":username, "text":$('#chat_line').val()};
        sendjson(data); 
        $('#chat_line').val(''); 
    }

    //send a message to the server (needs linefeed delimeter because sometimes records get concattenated)
    function sendjson(json_data) 
    {
        var jdata = $.toJSON(json_data); 
        try 
        {
            if (jdata.length < 10000)  // only concatenate for smallish strings
                conn.send(jdata + "\r\n");  
            else
            {
                conn.send(jdata);  
                conn.send("\r\n");  // this goes out in a second chunk
            }
        } 
        catch(err) 
        {
            if (!bSuppressDisconnectionMessages)
            {
                writeToConsole("Send error: " + err, "exceptionnoesc"); 
                writeToChat(jdata); 
            }
        }
    }

    //send code request run
    function sendCode() 
    {
        if ($('.editor_controls #run').attr('disabled'))
            return; 

        // protect not-ready case
        if ((conn == undefined) || (conn.readyState != conn.READY_STATE_OPEN)) 
        { 
            alert("Not ready, readyState=" + (conn == undefined ? "undefined" : conn.readyState)); 
            return; 
        }

    
        //send the data
        code = codeeditor.getCode(); 
        data = {
            "command"   : "run",
            "guid"      : guid,
            "username"  : username, 
            "userrealname" : userrealname, 
            "language"  : scraperlanguage, 
            "scrapername":short_name,
            "code"      : code,
            "urlquery"  : ($('#id_urlquery').hasClass('hint') ? '' : $('#id_urlquery').val())
        }
        $('.editor_controls #run').val('Sending');
        sendjson(data); 

        // do a save to the system every time we run (this would better be done via twisted at some point)
        var automode = $('select#automode option:selected').val(); 
        if (pageIsDirty && ((automode == 'autosave') || (automode == 'autotype')))
            saveScraper(); 
    } 


    function changeAutomode() 
    {
        lasttypetime = new Date(); 
        var automode = $('select#automode option:selected').val(); 
        if (automode == 'draft')
        {
            $('#watcherstatus').text("draft mode"); // consider also hiding select#automode
            setCodeeditorBackgroundImage('none')

        // You can never go back from draft mode. (what if someone else (including you) had edited?)
        // often you will do this in a duplicate window that you take into draft mode and then discard,
        // though the UI for making these duplicate windows is a pain as you have to fully close the editor, and then open two editors from the overview page
        // because you can't clone from the close window button as it's activated to disconnect the connection to the editor
        // Draft windows will be able to pop up a diff with the current saved version, so using this as a patch could readily provide a route back through a reload
            $('select#automode #id_autosave').attr('disabled', true); 
            $('select#automode #id_autoload').attr('disabled', true); 
            $('select#automode #id_autotype').attr('disabled', true); 
            $('.editor_controls #btnCommitPopup').attr('disabled', true); 
            $('.editor_controls #run').attr('disabled', false);
            $('.editor_controls #preview').attr('disabled', false);
        }
                // self demote from editing to watching
        else if (automode == 'autoload')
        {
            $('select#automode #id_autosave').attr('disabled', true); 
            $('select#automode #id_autotype').attr('disabled', true); 
            setCodeeditorBackgroundImage('url(/media/images/staff.png)')
            $('.editor_controls #btnCommitPopup').attr('disabled', true); 
            $('.editor_controls #run').attr('disabled', true);
            $('.editor_controls #preview').attr('disabled', true);
        }
        writeToChat('Changed automode: ' + automode); 

        data = {"command":'automode', "automode":automode}; 
        if ((automode == "autoload") && (loggedineditors.length >= 3))
            data["selectednexteditor"] = loggedineditors[iselectednexteditor]; 
        sendjson(data); 
    }; 

    function showhideAutomodeSelector()
    {
        var automode = $('select#automode option:selected').val(); 
        if ($('input#showautomode').attr('checked') || (automode == 'autotype') || (username ? (loggedineditors.length >= 2) : (loggedineditors.length >= 1)))
            $('select#automode').show(); 
        else
            $('select#automode').hide(); 
    }

    function parseISOdate(sdatetime) // used to try and parse an ISOdate, but it's highly irregular and IE can't do it
        {  return new Date(parseInt(sdatetime)); }

    function timeago(ctime, servernowtime)
    {
        var seconds = (servernowtime.getTime() - ctime.getTime())/1000; 
        return (seconds < 120 ? seconds.toFixed(0) + " seconds" : (seconds/60).toFixed(1) + " minutes"); 
    }

    function setwatcherstatusmultieditinguser()
    {
        if (iselectednexteditor >= loggedineditors.length)
            iselectednexteditor = 1; 
        var selectednexteditor = loggedineditors[iselectednexteditor]; 
        wstatus = '<a href="'+ $('input#userprofileurl').val().replace(/XXX/g, selectednexteditor) +'" target="_blank">'+selectednexteditor+'</a>'; 
        if (loggedineditors.length >= 3)
            wstatus += ' (<a class="plusone">+' + (loggedineditors.length-2) + '</a>)'; 
        wstatus += ' <a class="plusoneselect">is</a> watching'; 
        $('#watcherstatus').html(wstatus); 
        if (loggedineditors.length >= 3)
            $('#watcherstatus .plusone').click(function() { iselectednexteditor += 1; setwatcherstatusmultieditinguser() }); 
        $('#watcherstatus .plusoneselect').click(transmitSelection); 
    }

    // when the editor status is determined it is sent back to the server
    function recordEditorStatus(data) 
    { 
        var boutputstatus = (lasttouchedtime == undefined); 
        //console.log($.toJSON(data)); 
        if (data.nowtime)
            servernowtime = parseISOdate(data.nowtime); 
        if (data.earliesteditor)
            earliesteditor = parseISOdate(data.earliesteditor); 
        if (data.scraperlasttouch)
            lasttouchedtime = parseISOdate(data.scraperlasttouch); 

        editingusername = (data.loggedineditors ? data.loggedineditors[0] : '');  // the first in the list is the primary editor
        loggedineditors = data.loggedineditors;  // this is a list
        nanonymouseditors = data.nanonymouseditors; 
        chatname = data.chatname; 

        if (data.message)
            writeToChat('<i>'+cgiescape(data.message)+'</i>'); 

        if (boutputstatus)  // first time
        {
            stext = [ ]; 
            stext.push("Editing began " + timeago(earliesteditor, servernowtime) + " ago, last touched " + timeago(lasttouchedtime, servernowtime) + " ago"); 
            var othereditors = [ ]; 
            for (var i = 0; i < data.loggedineditors.length; i++) 
            {
                if (data.loggedineditors[i] != username)
                    othereditors.push(data.loggedineditors[i]); 
            }
            if (othereditors.length)
                stext.push("; Other editors: " + othereditors.join(", ")); 
            if (nanonymouseditors - (username ? 0 : 1) > 0) 
                stext.push("; there are " + (nanonymouseditors-(username ? 0 : 1)) + " anonymous editors watching"); 
            stext.push("."); 
            writeToChat(cgiescape(stext.join(""))); 
        }
        showhideAutomodeSelector(); 

        var automode = $('select#automode option:selected').val(); 

        // draft editing do not disturb
        if (automode == 'draft') 
        {
            ;
        }

        // you are the editing user
        else if (username && (editingusername == username))
        {
            $('select#automode #id_autoload').attr('disabled', (loggedineditors.length == 1)); // no point in being a watcher if no one else is available to edit

            if (loggedineditors.length >= 2)
                setwatcherstatusmultieditinguser(); // sets links to call self
            else
                $('#watcherstatus').html(""); 

            if (data.broadcastingeditor == username)   
            {
                    // convert all the autosaving pages to watching (apart from the one that the user changed to autotype)
                if (automode == 'autosave')
                {
                    $('select#automode #id_autoload').attr('disabled', false); 
                    $('select#automode').val('autoload'); // watching
                    $('select#automode #id_autosave').attr('disabled', false); 
                    $('select#automode #id_autotype').attr('disabled', true); 
                    setCodeeditorBackgroundImage('url(/media/images/staff.png)')
                    $('.editor_controls #btnCommitPopup').attr('disabled', true); 
                    $('.editor_controls #run').attr('disabled', true);
                    $('.editor_controls #preview').attr('disabled', true);
                    sendjson({"command":'automode', "automode":'autoload-nodemote'}); 
                }
            }
            else if (((automode != 'autosave') && (automode != 'autotype')) || (data.broadcastingeditor == undefined))
            {
                setCodeeditorBackgroundImage('none')
                $('select#automode #id_autosave').attr('disabled', false); 
                $('select#automode #id_autotype').attr('disabled', pageIsDirty); 
                $('select#automode').val('autosave'); // editing
                $('.editor_controls #run').attr('disabled', false);
                $('.editor_controls #preview').attr('disabled', false);
                $('.editor_controls #btnCommitPopup').attr('disabled', false); 
                sendjson({"command":'automode', "automode":'autosave'}); 
            }
        }

        // you are not the editing user, someone else is
        else if (editingusername)
        {
            $('#watcherstatus').html('<a href="'+$('input#userprofileurl').val().replace(/XXX/g, editingusername)+'" target="_blank">'+editingusername+'</a> <a class="plusoneselect">is</a> <a class="plusoneediting">editing</a>'); 
            if (username)
                $('#watcherstatus .plusoneediting').click(function() { sendjson({"command":'requesteditcontrol', "user":username}); }); 
            $('#watcherstatus .plusoneselect').click(transmitSelection); 

            if (automode != 'autoload')
            {
                $('select#automode #id_autoload').attr('disabled', false); 
                $('select#automode').val('autoload'); // watching
                $('select#automode #id_autosave').attr('disabled', true); 
                $('select#automode #id_autotype').attr('disabled', true); 
                setCodeeditorBackgroundImage('url(/media/images/staff.png)')
                $('.editor_controls #btnCommitPopup').attr('disabled', true); 
                $('.editor_controls #run').attr('disabled', true);
                $('.editor_controls #preview').attr('disabled', true);
                sendjson({"command":'automode', "automode":'autoload'}); 
            }
        }

        // you are not logged in and the only person looking at the scraper
        else
        {
            $('#watcherstatus').text(""); 
            if (automode != 'draft')
            {
                $('select#automode #id_autosave').attr('disabled', false); 
                $('select#automode #id_autotype').attr('disabled', true); 
                $('select#automode').val('autosave'); // editing
                $('select#automode #id_autoload').attr('disabled', true); 
                setCodeeditorBackgroundImage('none')
                $('.editor_controls #btnCommitPopup').attr('disabled', false); 
                $('.editor_controls #run').attr('disabled', false);
                $('.editor_controls #preview').attr('disabled', false);
                sendjson({"command":'automode', "automode":'autosave'}); 
            }
        }
    }

    function recordOtherTyping(chainpatch)
    {
        var linehandle = codeeditor.nthLine(chainpatch["insertlinenumber"]); 

        // change within a single line
        if ((chainpatch["deletions"].length == 1) && (chainpatch["insertions"].length == 1))
        {
            var linecontent = codeeditor.lineContent(linehandle); 
            var deletestr = chainpatch["deletions"][0]; 
            var insertstr = chainpatch["insertions"][0]; 
            if (linecontent != deletestr)
            {
                writeToChat("Lines disagree " + $.toJSON(chainpatch)); 
                writeToChat(linecontent); 
                writeToChat(deletestr); 
                return; 
            }

            codeeditor.setLineContent(linehandle, insertstr); 
            var ifront = 0; 
            while ((ifront < deletestr.length) && (ifront < insertstr.length) && (deletestr.charAt(ifront) == insertstr.charAt(ifront)))
                ifront++; 
            if (ifront < insertstr.length)
            {
                var iback = insertstr.length - 1; 
                while ((iback > ifront) && (iback - insertstr.length + deletestr.length > 0) && (deletestr.charAt(iback - insertstr.length + deletestr.length) == insertstr.charAt(iback)))
                    iback--; 
                codeeditor.selectLines(linehandle, ifront, linehandle, iback+1); 
            }

            else 
                codeeditor.selectLines(linehandle, ifront, codeeditor.nextLine(linehandle), 0); 
        }

        // change across multiple lines
        else
        {
            var insertions = chainpatch["insertions"]; 
            var deletions = chainpatch["deletions"]; 
            if (true) // check line content
            {
                var dlinehandle = linehandle; 
                for (var i = 0; i < deletions.length; i++)
                {
                    if (codeeditor.lineContent(dlinehandle) != deletions[i])
                    {
                        writeToChat("Lines " + i + " disagree " + $.toJSON(chainpatch)); 
                        writeToChat(codeeditor.lineContent(dlinehandle)); 
                        writeToChat(deletions[i]); 
                        return; 
                    }
                    dlinehandle = codeeditor.nextLine(dlinehandle); 
                }
            }

            // apply the patch
            var nlinehandle = linehandle; 
            var il = 0; 
            while ((il < deletions.length - 1) && (il < insertions.length))
            {
                codeeditor.setLineContent(nlinehandle, insertions[il]); 
                nlinehandle = codeeditor.nextLine(nlinehandle); 
                il++; 
            }
            if (il == insertions.length)
            {
                while (il < deletions.length)
                {
                    codeeditor.removeLine(nlinehandle); 
                    il++; 
                }
                nlinehandle = codeeditor.prevLine(nlinehandle); 
            }
            else
                codeeditor.setLineContent(nlinehandle, insertions.slice(il).join("\n"));  // all remaining lines replace the last line

            // find the selection range
            var ifront = 0; 
            while ((ifront < insertions[0].length) && (ifront < deletions[0].length) && (insertions[0].charAt(ifront) == deletions[0].charAt(ifront)))
                ifront++; 
            var finsertstr = insertions[insertions.length-1]; 
            var fdeletestr = deletions[deletions.length-1]; 
            var iback = finsertstr.length - 1; 
            while ((iback >= 0) && (iback - finsertstr.length + fdeletestr.length > 0) && (fdeletestr.charAt(iback - finsertstr.length + fdeletestr.length) == finsertstr.charAt(iback)))
                iback--; 
            if ((insertions.length == 0) && (iback < ifront))
                iback = ifront; 
            if (iback == finsertstr.length - 1)
            {
                nlinehandle = codeeditor.nextLine(nlinehandle); 
                iback = 0; 
            }
            codeeditor.selectLines(linehandle, ifront, nlinehandle, iback); 
        }
    }

    function startingrun(lrunID, luml, lchatname) 
    {
        //show the output area
        resizeControls('up');
        
        document.title = document.title + ' *'

        $('#running_annimation').show();
        runID = lrunID; 
        uml = luml; 

        //clear the tabs
        clearOutput();
        writeToConsole('Starting run ... ' + (isstaff ? " [on "+uml+"]" : "")); 
        writeToChat('<i>' + lchatname + ' runs scraper</i>'); 

        //unbind run button
        $('.editor_controls #run').unbind('click.run')
        $('.editor_controls #run').addClass('running').val('Stop');

        //bind abort button
        $('.editor_controls #run').bind('click.abort', function() 
        {
            sendjson({"command" : 'kill'}); 
            $('.editor_controls #run').val('Stopping');
            $('.editor_controls #run').unbind('click.abort');
            $('.editor_controls #run').bind('click.stopping', clearJunkFromQueue);
        });
    }
    
    function endingrun(content) 
    {
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
        uml = ''; 

        // suppress any more activity to the preview frame
        if (activepreviewiframe != undefined) {
            activepreviewiframe.document.close(); 
            activepreviewiframe = undefined; 
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

    function makeSelection(selrange)
    {
        var linehandlestart = codeeditor.nthLine(selrange.startline + 1); 
        var linehandleend = (selrange.endline == selrange.startline ? linehandlestart : codeeditor.nthLine(selrange.endline + 1)); 
        codeeditor.selectLines(linehandlestart, selrange.startoffset, linehandleend, selrange.endoffset); 
    }

    function transmitSelection()
    {
        var curposstart = codeeditor.cursorPosition(true); 

        var curposend = codeeditor.cursorPosition(false); 
        var selrange = { startline:codeeditor.lineNumber(curposstart.line)-1, startoffset:curposstart.character, 
                         endline:codeeditor.lineNumber(curposend.line)-1, endoffset:curposend.character }; 
        sendjson({"command":'giveselrange', "selrange":selrange, "username":username}); 
    }

    function reloadScraper()
    {
        $('.editor_controls #btnCommitPopup').val('Loading...').addClass('darkness');
        var reloadajax = $.ajax({ url: $('input#editorreloadurl').val(), async: false, type: 'POST', data: { oldcode: codeeditor.getCode() } }); 
        var reloaddata = $.evalJSON(reloadajax.responseText); 
        codeeditor.setCode(reloaddata.code); 
        rev = reloaddata.rev; 
        chainpatchnumber = 0; 
        //codeeditor.focus(); 
        if (reloaddata.selrange)
            makeSelection(reloaddata.selrange); 
        ChangeInEditor("reload"); 
        window.setTimeout(function() { $('.editor_controls #btnCommitPopup').val('save' + (wiki_type == 'scraper' ? ' scraper' : '')).removeClass('darkness'); }, 1100);  
    }; 


    function run_abort() 
    {
        runRequest = runScraper();
        $('.editor_controls #run').unbind('click.run');
        $('.editor_controls #run').addClass('running').val('Stop');
        $('.editor_controls #run').bind('click.abort', function() 
        {
            sendjson({"command" : 'kill'}); 
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
        $('.editor_controls #btnCommitPopup').live('click', function (){
            saveScraper();  
            return false;
        });
        
        $('.editor_controls #btnCommitPopup').val('save' + (wiki_type == 'scraper' ? ' scraper' : '')); 

        //close editor link
        $('#aCloseEditor, #aCloseEditor1, .page_tabs a').click(function ()
        {
            if (pageIsDirty && !confirm("You have unsaved changes, close the editor anyway?"))
                return false; 
            bSuppressDisconnectionMessages = true; 
            sendjson({"command":'loseconnection'});   //if (conn)  conn.close(); not as effective 
            return true;
        });

        $(window).unload( function () { 
            bSuppressDisconnectionMessages = true; 
            writeToConsole('window unload'); 
            sendjson({"command":'loseconnection'}); 
            //if (conn)  conn.close();  
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

    function popupPreview() 
    {
        if ($('.editor_controls #preview').attr('disabled'))
            return; 

        var urlquery = ($('#id_urlquery').hasClass('hint') ? '' : $('#id_urlquery').val()); 
        var viewurl = $('input#viewrunurl').val(); 
        var previewmessage = ''; 
        if (urlquery.length != 0) 
        {
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
    function saveScraper()
    {
        if ($('.editor_controls #btnCommitPopup').attr('disabled'))
            return; 

        var bSuccess = false;

        //if saving then check if the title is set (must be if guid is set)
        if(shortNameIsSet() == false)
        {
            var sResult = jQuery.trim(prompt('Please enter a title for your scraper'));
            if (sResult != false && sResult != '' && sResult != 'Untitled') 
            {
                $('#id_title').val(sResult);
                aPageTitle = document.title.split('|')
                document.title = sResult + ' | ' + aPageTitle[1]
                bSuccess = true;
            }
        }
        else
            bSuccess = true;

        if (!bSuccess)
            return; 

        atsavedundo = codeeditor.historySize().undo;  // update only when success
        var sdata = {
                        title           : $('#id_title').val(),
                        commit_message  : "cccommit",   // could get some use out of this if we wanted to
                        sourcescraper   : $('#sourcescraper').val(),
                        wiki_type       : wiki_type,
                        guid            : guid,
                        language        : scraperlanguage,
                        code            : codeeditor.getCode(),
                        earliesteditor  : earliesteditor.toUTCString(), // goes into the comment of the commit to help batch sessions
                    }

        $.ajax({ url:$('input#saveurl').val(), type:'POST', contentType:"application/json", dataType:"html", data:sdata, success:function(response) 
        {
            res = $.evalJSON(response);
            if (res.status == 'Failed')
            {
                alert("Save failed error message.  Shouldn't happen"); 
                return; 
            }

            // 'A temporary version of your scraper has been saved. To save it permanently you need to log in'
            if (res.draft == 'True')
                $('#divDraftSavedWarning').show();

            // server returned a different URL for the new scraper that has been created.  Now go to it (and reload)
            if (res.url && window.location.pathname != res.url)
                window.location = res.url;

            // ordinary save case.
            if (res.draft != 'True') 
            {
                $('.editor_controls #btnCommitPopup').val('Saved').addClass('darkness'); 
                window.setTimeout(function() { $('.editor_controls #btnCommitPopup').val('save' + (wiki_type == 'scraper' ? ' scraper' : '')).removeClass('darkness'); }, 1100);  
writeToChat("Saved rev number: " + res.rev); 
                if (bConnected)
                    sendjson({"command":'saved', "rev":res.rev}); 
            }
            ChangeInEditor("saved"); 
        },
        error: function(response)
        {
            alert('Sorry, something went wrong, please try copying your code and then reloading the page');
            writeToChat("Response error: " + response.responseText); 
        }});

        $('.editor_controls #btnCommitPopup').val('Saving ...');
    }

    function cgiescape(text) 
    {
        if (typeof text != 'string')
            return "&lt;NONSTRING&gt;"; // should convert on server
        return (text ? text.replace(/&/g, '&amp;').replace(/</g, '&lt;') : "");
    }

    
    function setupResizeEvents()
    {
        $(window).resize(onWindowResize);

        $("#codeeditordiv").resizable(
        {
            handles: 's',   
            autoHide: false, 
            start: function(event, ui) 
            {
                var maxheight = $("#codeeditordiv").height() + $(window).height() - $("#outputeditordiv").position().top;

                $("#codeeditordiv").resizable('option', 'maxHeight', maxheight);

                //cover iframe
                var oFrameMask = $('<div id="framemask"></div>');
                oFrameMask.css({ position: 'absolute', top: 0, left:0, background:'none', zindex: 200, width: '100%', height: '100%' }); 
                $(".editor_code").append(oFrameMask); 
            },
            stop: function(event, ui)  
            { 
                resizeCodeEditor(); 
                $('#framemask').remove();
            }
        }); 

        // bind the double-click (causes problems with the jquery interface as it doesn't notice the mouse exiting the frame
        // $(".ui-resizable-s").bind("dblclick", resizeControls);
    }

    function shortNameIsSet()
    {
        var sTitle = jQuery.trim($('#id_title').val());
        return sTitle != 'Untitled' && sTitle != '' && sTitle != undefined && sTitle != false;
    }


    function writeExceptionDump(exceptiondescription, stackdump, blockedurl, blockedurlquoted) 
    {
        if (stackdump) {
            for (var i = 0; i < stackdump.length; i++) {
                var stackentry = stackdump[i]; 
                sMessage = (stackentry.file !== undefined ? (stackentry.file == "<string>" ? stackentry.linetext : stackentry.file) : ""); 
                if (stackentry.furtherlinetext !== undefined) {
                    sMessage += " -- " + stackentry.furtherlinetext;
                }
                linenumber = (stackentry.file == "<string>" ? stackentry.linenumber : undefined); 
                writeToConsole(sMessage, 'exceptiondump', linenumber); 
                if (stackentry.duplicates > 1) {
                    writeToConsole("  + " + stackentry.duplicates + " duplicates", 'exceptionnoesc'); 
                }
            }
        }

        if (blockedurl) {
            sMessage = "The link " + blockedurl.substring(0,50) + " has been blocked. "; 
            sMessage += "Click <a href=\"/whitelist/?url=" + blockedurlquoted + "\" target=\"_blank\">here</a> for details."; 
            writeToConsole(sMessage, 'exceptionnoesc'); 
        } else {
            writeToConsole(exceptiondescription, 'exceptiondump'); 
        }
    }

    function writeRunOutput(sMessage) 
    {
        writeToConsole(sMessage, 'console'); 
        if ((activepreviewiframe != undefined) && (activepreviewiframe.document != undefined))
            activepreviewiframe.document.write(sMessage); 
    }

    function showTextPopup(sLongMessage) 
    {
        $.modal('<pre class="popupoutput">'+cgiescape(sLongMessage)+'</pre>', 
                {overlayClose: true, 
                 containerCss:{ borderColor:"#fff", height:"80%", padding:0, width:"90%", background:"#000", color:"#3cef3b" }, 
                 overlayCss: { cursor:"auto" }
                });
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


    function parsehighlightcode(sdata, lmimetype)
    {
        var cachejson; 
        try 
        {
            cachejson = $.evalJSON(sdata);
        } 
        catch (err) 
        {
            return { "objcontent": $('<pre class="popupoutput">Malformed json: ' + cgiescape(sdata) + "</pre>") }; 
        }

        if ((lmimetype != "text/html") || (cachejson["content"].length > 20000))
        {
            cachejson["objcontent"] = $('<pre>'+cgiescape(cachejson["content"]) + "</pre>"); 
            return cachejson; 
        }
        // could highlight text/javascript and text/css

        var lineNo = 1; 
        var cpnumbers= ($('input#popuplinenumbers').attr('checked') ? $('<div id="cp_linenumbers"></div>') : undefined); 
        var cpoutput = $('<div id="cp_output"></div>'); 
        function addLine(line) 
        {
            if (cpnumbers)
                cpnumbers.append(String(lineNo++)+'<br>'); 
            var kline = $('<span>').css('background-color', '#fae7e7'); 
            for (var i = 0; i < line.length; i++) 
                cpoutput.append(line[i]);
            cpoutput.append('<br>'); 
        }
        highlightText(cachejson["content"], addLine, HTMLMixedParser); 
        cachejson["objcontent"] = $('<div id="cp_whole"></div>'); 
        if (cpnumbers)
            cachejson["objcontent"].append(cpnumbers); 
        cachejson["objcontent"].append(cpoutput); 
        return cachejson; 
    }



    function popupCached(cacheid, lmimetype)
    {
        modaloptions = { overlayClose: true, 
                         overlayCss: { cursor:"auto" }, 
                         containerCss:{ borderColor:"#00f", "borderLeft":"2px solid black", height:"80%", padding:0, width:"90%", "text-align":"left", cursor:"auto" }, 
                         containerId: 'simplemodal-container' 
                       }; 

        var cachejson = cachehidlookup[cacheid]; 
        if (cachejson == undefined)
        {
            modaloptions['onShow'] = function() 
            { 
                $.ajax({type : 'POST', url  : $('input#proxycachedurl').val(), data: { cacheid: cacheid }, success: function(sdata) 
                {
                    cachejson = parsehighlightcode(sdata, lmimetype); 
                    if (cachejson["content"].length < 15000)  // don't cache huge things
                        cachehidlookup[cacheid] = cachejson; 

                    var wrapheight = $('.simplemodal-wrap').height(); 
                    $('.simplemodal-wrap #loadingheader').remove(); 
                    $('.simplemodal-wrap').append(cachejson["objcontent"]); 
                    $('.simplemodal-wrap').css("height", wrapheight + "px").css("overflow", "auto"); 
                }})
            }
            $.modal('<h1 id="loadingheader">Loading ['+cacheid+'] ...</h1>', modaloptions); 
        }
        else
            $.modal(cachejson["objcontent"], modaloptions); 
    }

    function writeToSources(sUrl, lmimetype, bytes, failedmessage, cached, cacheid, ddiffer) 
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
            smessage.push(bytes + ' bytes loaded'); 
            if (lmimetype.substring(0, 5) != "text/") 
                smessage.push("<b>"+lmimetype+"</b>"); 
            if (cacheid != undefined)
                smessage.push('<a id="cacheid-'+cacheid+'" title="Popup html" class="cachepopup">&nbsp;&nbsp;</a>'); 
            if (cached == 'True')
                smessage.push('(from cache)'); 
        }
        else
            smessage.push(failedmessage); 
        if (ddiffer == "True")
            smessage.push('<span style="background:rad"><b>BAD CACHE</b></span>'); 

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
        })

        
        $('#output_data table.output_content').append(oRow);  // oddly, append doesn't work if we add tbody into this selection

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
                $('.editor_output div.tabs li.chat').addClass('chatalert');
                window.setTimeout(function() { $('.editor_output div.tabs li.chat').removeClass('chatalert'); }, 1500); 
            }
        }
    }

    // some are implemented with tables, and some with span rows.  
    function setTabScrollPosition(sTab, command) 
    {
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

   
   
});
