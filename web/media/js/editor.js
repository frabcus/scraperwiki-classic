$(document).ready(function() {
    
    //variables
    var editor_id = 'id_code';
    var codeeditor;
    var draggedWindow; // the iframe that needs resizing
    var draggedwindowheightdiff; // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
    var previouscodeeditorheight;    // saved for the double-clicking on the drag bar
    var short_name = $('#scraper_short_name').val();
    var guid = $('#scraper_guid').val();
    var run_type = $('#code_running_mode').val();

    //constructor functions
    setupCodeEditor();
    setupMenu();
    setupTabs();
    setupPopups();
    setupToolbar()
    setupDetailsForm();
    setupAutoDraft();
    setupResizeEvents();


    //setup code editor
    function setupCodeEditor(){
        codeeditor = CodeMirror.fromTextArea("id_code", {
            parserfile: ["../contrib/python/js/parsepython.js"],
            stylesheet: "/media/CodeMirror-0.63/contrib/python/css/pythoncolors.css",
            path: "/media/CodeMirror-0.63/js/",
            textWrapping: false,
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
                  action : 'save',
                  }),
                dataType: "html",
                success: function(){
                        // Attempt at niceish notification, it needs work though ;)
                         $('#notifications').fadeOut(800, function() {
                           $('#notifications').html('saved');
                           $('#notifications').fadeIn(800);                       
                           writeToConsole('Saved')
                         });                     
                      }
                  });
              },
            initCallback: function() {
                    draggedWindow = $("#id_code").next().children(":first"); 
                    draggedwindowheightdiff = draggedWindow.height() - $("#codeeditordiv").height(); 
                    onWindowResize();
                }, 
          });        
    }

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
        
        //assign events
        $('.editor_output .console a').click(function(){
            showTab('console');
        })
        $('.editor_output .data a').click(function(){
            showTab('data');
        })
        $('.editor_output .sources a').click(function(){
            showTab('sources');
        })

        //show default tab
        showTab('console'); //todo: check in cookie if tab already set.
        
    }
    
    //Setup Popups
    function setupPopups(){
        
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
                    height: $(window).height(),
                });
                $('#popups #overlay').fadeIn("fast")

            } else {
                this.style.display = "none";
            }
        });
    }

    //show feedback massage
    function showFeedbackMessage(sMessage){
       $('#feedback_messages').append(sMessage)
       $('#feedback_messages').slideToggle(200);
       setTimeout('$("#feedback_messages").slideToggle();', 1500);
    }
    
    //Setup save / details forms
    function setupDetailsForm(){

        // Meta form
        $('#meta_fields_mini').appendTo($('#meta_form'))
        $('#meta_fields_mini').attr('id', 'meta_fields')
        $('#id_title').after('<a href="" id="meta_form_edit">Edit scraper info</a>')

        $('#meta_form_edit').click(function() {
            // Only add the save button if it's not there already
            if (!$('#meta_form #save').length) {
                $('#save').clone().appendTo($('#meta_form'))
            }
            showPopup('meta_form')
            return false
        });
        
    }
    
    //Setup toolbar
    function setupToolbar(){
        
        //commit button
        $('#commit').click(
            function (){
                showPopup('meta_form')
                return false
            }
        );
        
        //save button
        $('#save').click(
           function(){
                saveScraper();
                return false;
           }
        );
        
        //clear console button
        $('#clear').click(function() {
            c = $('body', $('#console').contents())
            c.fadeOut("fast",
            function(){
                $('body', $('#console').contents()).html('')
            })
            c.fadeIn()
        });
        
        //diff button
         $('.editor_controls #notifications').before('<input type="button" value="Diff committed version" name="diff" id="diff" />');
         $('.editor_controls #diff').click(
             function() {
                 $.ajax({
                     type: 'POST',
                     url: '/editor/diff/' + short_name,
                     data: ({
                         code: codeeditor.getCode(),
                         }),
                     dataType: "html",
                     success: function(diff) {
                         $('#diff pre').text(diff);
                         showPopup('diff');
                     }
                 });
            }
        );
        
        // run button
        $('.editor_controls #notifications').before('<input type="button" value="Run" name="run" id="run" />');
        $('.editor_controls #run').click(function() {

            //reset the tabs
            $('.editor_output div.tabs li').removeClass('new');

            //set a dividers on the output
            $('#output_console div :last-child').addClass("run_end")
            $('#output_data div :last-child').addClass("run_end")
            $('#output_sources div :last-child').addClass("run_end")                


            //run either the firestarter or run mdoel
            if (run_type == 'firestarter_apache') {

                $('#editor').bind('form-pre-serialize', null,
                function(foo, options) {
                    $('#editor #id_code').text(codeeditor.getCode())
                })

                $('#editor').ajaxSubmit({
                    target: '#console',
                    action: '/editor/run_code',
                });

                return false;
                // <-- important!
            } else {
                $.ajax({
                    type: 'POST',
                    url: '/editor/run_code',
                    data: ({
                        code: codeeditor.getCode(),
                        guid: guid,
                    }),
                    dataType: "html",
                    success: function(code) {        

                        //split results
                        var aResults = code.split("@@||@@");
                        for (var i=0; i < aResults.length -1; i++) {
                            var oItem = eval('(' + aResults[i] + ')')
                            if(oItem.message_type == 'sources'){                                                        
                                writeToSources(oItem.content);                                                            
                            }else if (oItem.message_type == 'data'){
                                writeToData(oItem.content);                                
                            }else{                            
                                writeToConsole(oItem.content);    
                            }
                        };
                    }
                });
            }

        });

    }

    //Save
    function saveScraper(){

        var bSuccess = false;

        if(shortNameIsSet() == false){
            var sResult = jQuery.trim(prompt('Please enter a title for your scraper'));

            if(sResult != false && sResult != '' && sResult != 'Untitled Scraper'){
                $('#id_title').val(sResult);
                bSuccess = true;
            }
        }

        if(bSuccess == true){
            $.ajax({
              type : 'POST',
              URL : window.location.pathname,
              data: ({
                title : $('#id_title').val(),
                code : codeeditor.getCode(),
                action : 'save',
                }),
              dataType: "html",
              success: function(response){
                      // Attempt at niceish notification, it needs work though ;)
                       $('#notifications').fadeOut(800, function() {
                         $('#notifications').html('saved');
                         $('#notifications').fadeIn(800);                       
                         writeToConsole('Saved')
                       });                     
                    }
                });
            }
    }

    //Show random text popup
    function showTextPopup(sMessage){
        $('#popup_text').append(sMessage);
        showPopup('popup_text');
    }
    
    function setupResizeEvents(){
        $(window).resize(onWindowResize);
    }

    function shortNameIsSet(){
        var sTitle = jQuery.trim($('#id_title').val());
        return sTitle != 'Untitled Scraper' && sTitle != '' && sTitle != undefined && sTitle != false;
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
    }

    function setupAutoDraft(){
        // auto save a draft
          setInterval(function() {
              $.ajax({
                  type: 'POST',
                  URL: window.location.pathname,
                  data: ({
                      title: $('#id_title').val(),
                      code: codeeditor.getCode(),
                      action: 'save',
                  }),
                  dataType: "html",
                  success: function() {
                      // Attempt at niceish notification, it needs work though ;)
                      $('#notifications').fadeOut(800,
                      function() {
                          $('#notifications').html('Draft Auto Saved');
                          $('#notifications').fadeIn(800);
                          // wirteToConsole('Auto Saved')
                      });

                  }
              })
          },
          60000);    
    }

    //Write to concole/data/sources
    function writeToConsole(sMessage) {

        sDisplayMessage = sMessage;
        if(sMessage.length > 200){
            sDisplayMessage = sMessage.substring(0, 200);
            sDisplayMessage += '&nbsp;<a href="#" onclick="showTextPopup(' + "'" + 'hello' + "'" + ')>...</a>';
        }

        $('#output_console :first').append('<span class="output_item">' + sDisplayMessage + "</span>");
        $('.editor_output div.tabs li.console').addClass('new');
        
    }
    
    function writeToSources(sMessage) {

        $('#output_sources :first').append(sMessage);
        $('.editor_output div.tabs li.sources').addClass('new');
        
    }
    
    function writeToData(sMessage) {

        $('#output_data :first').append(sMessage);
        $('.editor_output div.tabs li.data').addClass('new');
        
    }

    //show tab
    function showTab(sTab){
        $('.editor_output .info').children().hide();
        $('#output_' + sTab).show();

        $('.editor_output div.tabs ul').children().removeClass('selected');
        $('.editor_output div.tabs li.' + sTab).addClass('selected');
    }

    //resize code editor
   function resizeCodeEditor(){
      if (draggedWindow)
          draggedWindow.height(($("#codeeditordiv").height() + draggedwindowheightdiff) + 'px'); 
    };

    //click bar to resize
    function clickToResize() {
      var maxheight = $("#codeeditordiv").height() + $(window).height() - $("#outputeditordiv").position().top; 
      if (maxheight >= $("#codeeditordiv").height() + 5)
      {
          previouscodeeditorheight = $("#codeeditordiv").height(); 
          $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor); 
      }
      else

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
         $(".ui-resizable-s").bind("dblclick", clickToResize);



       function onWindowResize() {
           var maxheight = $("#codeeditordiv").height() + $(window).height() - $("#outputeditordiv").position().top; 
           if (maxheight < $("#codeeditordiv").height())
             $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor); 
         };
   
   
});