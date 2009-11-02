$(document).ready(function() {

    //setup click events for tabs
    $('.editor_output .console a').click(function(){
        showTab('console');
    })
    $('.editor_output .data a').click(function(){
        showTab('data');
    })
    $('.editor_output .sources a').click(function(){
        showTab('sources');
    })

    //set default tab
    showTab('console');

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

    $(document).keypress(function(e) {
        if (e.keyCode == 27 && popupStatus == 1) {
            hidePopup();
        }
    });

    $('.popupClose').click(function() {
        hidePopup();
    })

    $('#overlay').click(function() {
        hidePopup();
    })

    function hidePopup() {
        // Hide popups
        $('#popups div.popup_item').each(function(i) {
            $(this).fadeOut("fast")
        });

        // Hide overlay
        $('#popups #overlay').fadeOut("fast")
        popupStatus = 0;
    }


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


    // clear console
    $('#clear').click(function() {
        c = $('body', $('#console').contents())
        c.fadeOut("fast",
        function() {
            $('body', $('#console').contents()).html('')
        })
        c.fadeIn()
    });


    // Diff button
    $('.editor_controls #notifications').before('<input type="button" value="Diff committed version" name="diff" id="diff" />');
    $('.editor_controls #diff').click(function() {
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
    });

    // Run button
    $('.editor_controls #notifications').before('<input type="button" value="Run" name="run" id="run" />');
    $('.editor_controls #run').click(function() {

        //reset the tabs
        $('.editor_output div.tabs li').removeClass('new');
        
        //set a dividers on the output
        $('#output_sources div :last-child').addClass ("run_end")
        
        
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

    function writeToConsole(sMessage) {

        $('#output_console :first').append('<span class="output_item">' + sMessage + "</span>");
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

    function showTab(sTab){
        $('.editor_output .info').children().hide();
        $('#output_' + sTab).show();
        
        $('.editor_output div.tabs ul').children().removeClass('selected');
        $('.editor_output div.tabs li.' + sTab).addClass('selected');
    }

});
