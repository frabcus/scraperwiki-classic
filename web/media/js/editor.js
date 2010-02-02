$(document).ready(function() {
    
    //variables
    var pageIsDirty = false;
    var editor_id = 'id_code';
    var codeeditor;
    var codemirroriframe; // the iframe that needs resizing
    var codemirroriframeheightdiff; // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var previouscodeeditorheight;    // saved for the double-clicking on the drag bar
    var short_name = $('#scraper_short_name').val();
    var guid = $('#scraper_guid').val();
    var run_type = $('#code_running_mode').val();
    var codemirror_url = $('#codemirror_url').val();
    var conn; // Orbited connection
    var buffer = "";
    var selectedTab = 'console';
    var outputMaxItems = 400;

    //constructor functions
    setupCodeEditor();
    setupMenu();
    setupOrbited();
    setupTabs();
    setupPopups();
    setupToolbar();
    setupDetailsForm();
    setupAutoDraft();
    setupResizeEvents();
    setupKeygrabs();   

    //setup code editor
    function setupCodeEditor(){
        codeeditor = CodeMirror.fromTextArea("id_code", {
            parserfile: ["../contrib/python/js/parsepython.js"],
            stylesheet: codemirror_url + "contrib/python/css/pythoncolors.css",
            path: codemirror_url + "js/",
            textWrapping: true,
            lineNumbers: true,
            indentUnit: 4,
            readOnly: false,
            tabMode: "spaces", 
            autoMatchParens: true,
            width: '100%',
            parserConfig: {'pythonVersion': 2, 'strictErrors': true},
            saveFunction: function () {    // this is your Control-S function
              $.ajax({
                type : 'POST',
                URL : window.location.pathname,
                data: ({
                  title : $('#id_title').val(),
                  code : codeeditor.getCode(),
                  action : 'save'
                  }),
                dataType: "html",
                success: function(){
                    
                      }
                  });
              },
              
            onChange: function (){
                pageIsDirty = true; // note that code has changed
            },

            // this is called once the codemirror window has finished initializing itself
            initCallback: function() {
                    codemirroriframe = $("#id_code").next().children(":first"); 
                    codemirroriframeheightdiff = codemirroriframe.height() - $("#codeeditordiv").height(); 
                    onWindowResize();
                    pageIsDirty = false; // page not dirty at this point
                    
                } 
          });        
    }


    
    function setupOrbited() {
        TCPSocket = Orbited.TCPSocket;
        conn = new TCPSocket()
        conn.open('localhost', '9010')
    }
    
    //Setup Keygrabs

    function setupKeygrabs(){

        addHotkey('ctrl+r', sendCode);       
        addHotkey('ctrl+s', saveScraper); 
        addHotkey('ctrl+d', viewDiff);                       
          
    };

    
    //Setup Menu
    function setupMenu(){
        $('#menu_shortcuts').click(function(){
           showPopup('popup_shortcuts'); 
        });
        $('#menu_settings').click(function(){
           showPopup('popup_settings'); 
        });
        $('#menu_documentation').click(function(){
           showPopup('popup_documentation'); 
        });        
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

        //show default tab
        showTab('console'); //todo: check in cookie if tab already set.
        
        resizeControls('up');
    }
    
    //Setup Popups
    function setupPopups(){
        popupStatus = 0
        //assign escape key to close popups
        $(document).keypress(function(e) {
            if (e.keyCode == 27 && popupStatus == 1) {
                hidePopup();
            }
        });

        //setup evnts
        $('.popupClose').click(
            function() {
                hidePopup();
            }
        );

        $('#overlay').click(
            function() {
                hidePopup();
            }
        );   
    }

    function showPopup(sId) {

        //show or hide the relivant block
        $('#popups div.popup_item').each(function(i) {
            if (this.id == sId) {
                
                if (sId == 'meta_form') {
                    $('#id_meta_title').val($('#id_title').val())
                }
                
                popupStatus = 1;
                //show
                $(this).css({
                    // display:'block',
                    height: $(window).height() - 200,
                    position: 'absolute'
                });
                $(this).fadeIn("fast")

                //add background
                $('#popups #overlay').css({
                    width: $(window).width(),
                    height: $(window).height()
                });
                $('#popups #overlay').fadeIn("fast")

            } else {
                this.style.display = "none";
            }
        });
    }

    //show feedback massage
    function showFeedbackMessage(sMessage){
       $('#feedback_messages').html(sMessage)
       $('#feedback_messages').slideToggle(200);
       setTimeout('$("#feedback_messages").slideToggle();', 2500);
    }

    //Setup save / details forms
    function setupDetailsForm(){
        
        //sync title text boxes
        $('#id_meta_title').keyup(
                function(){
                    $('#id_title').val($('#meta_form #id_meta_title').val());
                }
            );
        
        // Meta form
        $('#meta_fields_mini').appendTo($('#meta_form'))
        $('#meta_fields_mini').attr('id', 'meta_fields')
        $('#id_title').before('<a href="" id="meta_form_edit"><img src="/media/images/icons/information.png" alt="Edit scraper information" title="Edit scraper information"/></a>')
        $('#meta_form_edit').click(function() {            

            // Only add the save button if it's not there already
            /*
            if (!$('#meta_form .save').length) {
                $('.save').clone().appendTo($('#meta_form'));
            };
            */
            showPopup('meta_form');
            return false;
        });

    }

/*
    conn.onclose = function(){
        alert('connection closed');
    }
*/
    //read data back from twisted

    conn.onread = function(data) {
      // check if this data is valid JSON, or add it to the buffer
      try {
        data = buffer+data;
        buffer = "";
        json_data = '{"lines": [' + data + ']}';
        all_data = eval('('+json_data+')');      
        lines = all_data.lines
      
        for (var i=0, len=lines.length; i<len; ++i ) {          
              data = lines[i];
          if (data.message_type == "kill" || data.message_type == "end") {
              $('.editor_controls #run').removeClass('running').val('run');
              $('.editor_controls #run').unbind('click.abort');
              $('.editor_controls #run').bind('click.run', sendCode);

            //change title
            document.title = document.title.replace('*', '')

            //hide annimation
            $('#running_annimation').hide();

          } else if (data.message_type == "sources") {
              writeToSources(data.content, data.url)
          } else if (data.message_type == "data") {
              writeToData(data.content)
          } else if (data.message_type == "exception") {
              sMessage = data.content;
              iLineNumber = 0;
              if(parseInt(data.lineno) > 0){
                 iLineNumber = data.lineno;
                 codeeditor.selectLines(codeeditor.nthLine(iLineNumber), 0);                 
              }
              writeToConsole(sMessage, data.content_long, data.message_type, iLineNumber)
          } else {
              writeToConsole(data.content, data.content_long, data.message_type)
          }
        }        
      } catch(err) {
        //console.debug(err)
        buffer +=data;
      }
    }

    //send a message to the server
    function send(json_data) {
      conn.send(
        JSON.stringify(json_data)
        );  
    }

    //send a 'kill' message
    function sendKill() {
      data = {
        "command" : 'kill',
      }
      send(data)
    }

    //send code request run
    function sendCode() {

        //show the output area
        resizeControls('up');
        
        //chaneg docuemnt title
        document.title = document.title + ' *'
        
        //hide annimation
        $('#running_annimation').show();
    
        //clear the tabs
        clearOutput();
    
          //send the data
          data = {
            "command" : "run",
            "guid" : guid,
            "code" : codeeditor.getCode()
          }
          send(data)

          //unbind run button
          $('.editor_controls #run').unbind('click.run')
          $('.editor_controls #run').addClass('running').val('Stop');

          //bind abort button
          $('.editor_controls #run').bind('click.abort', function() {
              sendKill();
              $('.editor_controls #run').removeClass('running').val('run');
              $('.editor_controls #run').unbind('click.abort')
              $('.editor_controls #run').bind('click.run', sendCode);

              //hide annimation
              $('#running_annimation').hide();
  
              //change title
              document.title = document.title.replace(' *', '')
          });
  
      
      
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
                $('#diff pre').text(diff);
                showPopup('diff');
            }
        });
    }

    function clearOutput(){
        $('#output_console div').html('');    
        $('#output_sources div').html('');    
        $('#output_data table').html('');                    
    }

    function reloadScraper(){
        if (shortNameIsSet() == false){
            $('#diff pre').text("Cannot reload draft scraper");
            showPopup('diff');
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
        var selrange = [0,0,0,0]
        if (iselrangedelimeter != -1){
            var selrange = newcode.substring(0, iselrangedelimeter); 
            newcode = newcode.substring(iselrangedelimeter + selrangedelimeter.length); 
            selrange = eval(selrange); 
        }

        codeeditor.setCode(newcode); 
        codeeditor.focus(); 

        // make the selection
        if (!((selrange[2] == 0) && (selrange[3] == 0))){
            linehandlestart = codeeditor.nthLine(selrange[0] + 1); 
            linehandleend = codeeditor.nthLine(selrange[2] + 1); 
            codeeditor.selectLines(linehandlestart, selrange[1], linehandleend, selrange[3]); 
        }
    }; 


    function run_abort() {
            runRequest = runScraper();
            $('.editor_controls #run').unbind('click.run')
            $('.editor_controls #run').addClass('running').val('Stop');
            $('.editor_controls #run').bind('click.abort', function() {
                sendKill()
                $('.editor_controls #run').removeClass('running').val('run');
                $('.editor_controls #run').unbind('click.abort')                    
                writeToConsole('Run Aborted') // Custom function that append to a div
                $('.editor_controls #run').bind('click.run', run_abort);
                
                //hide annimation
                $('#running_annimation').hide();
                
                //change title
                document.title = document.title.replace(' *', '')
            });
            
        }
    
    
    //Setup toolbar
    function setupToolbar(){
        
        //commit button
        $('.commit').live('click', function (){
            if (popupStatus == 0) {
                // Only add the save button if it's not there already
                if (!$('#meta_form .commit').length) {
                    $('.commit').clone().appendTo($('#meta_form'));
                };
                
                showPopup('meta_form');
                return false;     
            }
            if ($('#meta_form #id_commit_message').val() == ""){
                $('#meta_form #id_commit_message').effect('highlight')
                return false
            } else {
                saveScraper(true);
                return false;                
            }

            }
        );
        
        //save button
        $('.save').live('click', function(){
             saveScraper(false);
             return false;
        });
        
        // run button
        $('.editor_controls #run').bind('click.run', sendCode);

        //diff button
         $('.editor_controls #diff').click(function() {
                viewDiff(); 
                return false; 
            }
        ); 

        //diff button
         $('.editor_controls #reload').click(function() {
                reloadScraper(); 
                return false; 
            }
        );

        //close editor link
        $('#aCloseEditor').click(
            function (){
                var bReturn = true;
                if (pageIsDirty){
                    if(confirm("You have unsaved changes, close the editor anyway?") == false){
                        bReturn = false
                    }
                }

                return bReturn;
            }
        );
    }

    //commit
    function commitScraper(){
        return true;
        /*
        $.ajax({
          type : 'POST',
          URL : window.location.pathname,
          data: ({
            title : $('#id_title').val(),                        
            code : codeeditor.getCode(),
            action : 'commit',
            }),
          dataType: "html",
          success: function(response){
                showFeedbackMessage("Your changes have been committed");
            },
        error: function(response){
            alert('Sorry, something went wrong committing your scraper');
          }
        });
        */
    }
    
    //Save
    function saveScraper(bCommit){
        var bSuccess = false;

        // make sure the title is the same as the popup
        if (popupStatus == 1){            
            $('#id_title').val($('#id_meta_title').val())
        }

        //if saving then check if the title is set
        if(shortNameIsSet() == false && bCommit != true){
            var sResult = jQuery.trim(prompt('Please enter a title for your scraper'));

            if(sResult != false && sResult != '' && sResult != 'Untitled Scraper'){
                $('#id_title').val(sResult);
                aPageTitle = document.title.split('|')
                document.title = sResult + ' | ' + aPageTitle[1]
                bSuccess = true;
            }
        }else{
            bSuccess = true;
        }
        
        form_action = 'save';
        if (bCommit == true) {
            form_action = 'commit';
        }

        if(bSuccess == true){
            $.ajax({
              type : 'POST',
              contentType : "json",
              URL : window.location.pathname,
              data: ({
                title : $('#id_title').val(),
                tags : $('#id_tags').val(),
                license : $('#id_license').val(),
                description : $('#id_description').val(),                
                code : codeeditor.getCode(),
                action : form_action
                }),
              dataType: "html",
              success: function(response){
                    res = eval('('+response+')');
                    if (res.url && window.location.pathname != res.url) {
                        window.location = res.url;
                    };

                    if (bCommit != true){                        
                        showFeedbackMessage("Your scraper has been saved. Click <em>Commit</em> to publish it.");
                    }
                    
                    pageIsDirty = false; // page no longer dirty
                },

            error: function(response){
                alert('Sorry, something went wrong');
              }
            //error:function (xhr, ajaxOptions, thrownError){
             //       alert(xhr.responseText);
              //} 
            });
        }
    }

    //Show random text popup
    function showTextPopup(sMessage, sMessageType){
        $('#popup_text .output pre').text(sMessage);
        showPopup('popup_text');
    }
    
    //show exception popup
    function showExceptionPopup(sTitle, sException){
        $('#popup_exception h3').html(sTitle);
        $('#popup_exception .output pre').html(sException);
        showPopup('popup_exception');
    }
    
    function setupResizeEvents(){
        $(window).resize(onWindowResize);
    }

    function shortNameIsSet(){
        // Because of jquery example
        if ($('#id_title').hasClass('example')) {
            return false;
        }
        var sTitle = jQuery.trim($('#id_title').val());
        return sTitle != 'Untitled Scraper' && sTitle != '' && sTitle != undefined && sTitle != false;
    }

    //Hide popup
    function hidePopup() {

        $('#meta_form .button').remove()
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

    function setupAutoDraft(){
        /*
        // auto save a draft
          setInterval(function() {
              if (shortNameIsSet()){
                  $.ajax({
                      type: 'POST',
                      URL: window.location.pathname,
                      data: ({
                          title: $('#id_title').val(),
                          code: codeeditor.getCode(),
                          action: 'save'
                      }),
                      dataType: "html"
                  });                  
              }
          },
          60000);    
        */
    }

    //Write to concole/data/sources
    function writeToConsole(sMessage, sLongMessage, sMessageType, iLine) {

        // if an exception set the class accordingly
        sShortClassName = '';
        sLongClassName = 'message_expander';
        sExpand = '...more'
        if (sMessageType == 'exception'){
            sShortClassName = 'exception';
            sLongClassName = 'exception_expander';
            sExpand = 'view traceback'
            if(iLine){
               sMessage = ('Line ' + iLine + ': ' +  sMessage);                
            }

        }   


        //create new item
        oConsoleItem = $('<span></span>');
        oConsoleItem.addClass('output_item');
        oConsoleItem.addClass(sShortClassName);
        
        //add text
        oConsoleItem.html(sMessage);        
        if(sLongMessage != undefined){
            
            //expand link
            oMoreLink = $('<a href="#"></a>');
            oMoreLink.addClass('expand_link');
            oMoreLink.text(sExpand)
            oMoreLink.longMessage = sLongMessage;
            //add event
            if (sMessageType == 'exception'){
                oMoreLink.click(
                        function(){
                            showExceptionPopup(sMessage, sLongMessage);
                        }
                    );
            }else{
                oMoreLink.click(
                        function(){
                            showTextPopup(sLongMessage);
                        }
                    );                
            }
            oConsoleItem.append(oMoreLink);
        }
        
        //remove items if over max
        if ($('#output_console .output_content').children().size() >= outputMaxItems){
            $('#output_console .output_content').children(':first').remove();
        }

        //append to console
        $('#output_console .output_content').append(oConsoleItem);
        $('.editor_output div.tabs li.console').addClass('new');
        $('#output_console div').animate({ 
            scrollTop: $('#output_console .output_content').height()+$('#output_console div')[0].scrollHeight 
        }, 0);
        
        
    };


    function writeToSources(sMessage, sUrl) {

        sDisplayMessage = sMessage;

        $('#output_sources .output_content')
        //.append('<span class="output_item message_expander">' + sDisplayMessage + "</span>");
        .append('<span class="output_item"><a href="' + sUrl + '" target="_new">' + sUrl + '</a></span>')

        $('.editor_output div.tabs li.sources').addClass('new');
        $('#output_sources div').animate({ 
            scrollTop: $('#output_sources .output_content').height()+$('#output_sources div')[0].scrollHeight 
        }, 0);
    }

    function writeToData(sMessage) {
        row = eval(sMessage)

        html_row = "<tr>"
        $.each(row, function(i){
            html_row +="<td>"+row[i]+"</td>"
        })
        html_row += "</tr>"
        
        $('#output_data :first').append(html_row);
        $('.editor_output div.tabs li.data').addClass('new');
        
        
        $('#output_data').animate({ 
            scrollTop: $('#output_data').height()+$('#output_data')[0].scrollHeight 
        }, 0);
    }

    //show tab
    function showTab(sTab, bRevert){
        $('.editor_output .info').children().hide();
        $('.editor_output .controls').children().hide();        
        $('#output_' + sTab).show();
        $('#controls_' + sTab).show();

        $('.editor_output div.tabs ul').children().removeClass('selected');
        $('.editor_output div.tabs li.' + sTab).addClass('selected');
        
    }
    
    //show text tab
    function showTextTab(sTab){
        $('#popup_text .output').hide();
        $('#popup_text .popup_' + sTab).show();

        $('#popup_text div.tabs ul').children().removeClass('selected');
        $('#popup_text div.tabs li.' + sTab+'_tab').addClass('selected');
    }

    //resize code editor
   function resizeCodeEditor(){
      if (codemirroriframe){
          //resize the iFrame inside the editor wrapping div
          codemirroriframe.height(($("#codeeditordiv").height() + codemirroriframeheightdiff) + 'px');
          //resize the output area so the console scrolls correclty
          iWindowHeight = $(window).height();
          iEditorHeight = $("#codeeditordiv").height();
          iControlsHeight = $('.editor_controls').height()
          iCodeEditorTop = parseInt($("#codeeditordiv").position().top);
          $("#outputeditordiv").height(iWindowHeight - (iEditorHeight + iControlsHeight + iCodeEditorTop) + 'px');   
          $("#outputeditordiv .info").height($("#outputeditordiv").height() - parseInt($("#outputeditordiv .info").position().top) + 'px');
      }
    };
    

    //click bar to resize
    function resizeControls(sDirection) {
    
        if (sDirection != 'up' && sDirection != 'down'){
            sDirection = 'none';
        }

      //work out which way to go
      var maxheight = $("#codeeditordiv").height() + $(window).height() - ($("#outputeditordiv").position().top + 5); 
      if (maxheight >= $("#codeeditordiv").height() + 5 && (sDirection == 'none' || sDirection == 'down')) {
          previouscodeeditorheight = $("#codeeditordiv").height();
          $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor); 
      } else if (sDirection == 'none' || sDirection == 'up') {

          $("#codeeditordiv").animate({ height: Math.min(previouscodeeditorheight, maxheight - 5) }, 100, "swing", resizeCodeEditor); 

      };

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

         // bind the double-click 
         $(".ui-resizable-s").bind("dblclick", resizeControls);
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
