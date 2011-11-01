/*

function reload_scraper_attachables(short_name, redirect)
{
    $('#attachables_loading').show();
    $.ajax(
        {
            url:document.location,
            cache: false,
            type: 'GET', 
            success:function(htmlpage){
                $("#scraper_attachables").html($(htmlpage).find("#scraper_attachables").html())
                $("#header_inner").html($(htmlpage).find("#header_inner").html())
                setupChangeAttachables(short_name); 
                $('#attachables_loading').hide();
            },
            error: function(jq, textStatus, errorThrown){
                if ( redirect ) {
                    window.location.href = redirect;
                    return false;
                }

                alert( textStatus );
                alert( errorThrown );
            }
        });

    // original action: 
    //    document.location.reload(true);
}




function changeRoles(sdata, redirect_to_on_fail) {
    $.ajax(
		{
			url:$("#admincontroleditors").val(), 
			type: 'GET', 
			data:sdata, 
			success:function(result)
        	{
            	if (result.substring(0, 6) == "Failed")
                	$('#contributorserror').text(result).show(300);
            	else 
                	reload_scraper_contributors(redirect_to_on_fail); 
        	},
        	error:function(jq, textStatus, errorThrown)
        	{
            	$('#contributorserror').text("Connection failed: " + textStatus + " " + errorThrown).show(300);
        	}
		}
	); 	
}

function setupChangeEditorStatus()
{
    // changing editor status
    $('#addneweditor a').live('click', function()
    {
        $('#addneweditor a').hide()
        $('#addneweditor span').show(); 
        $('#contributorserror').hide();
    }); 
    $('#addneweditor input.cancelbutton').live('click', function()
    {
        $('#addneweditor span').hide(); 
        $('#addneweditor a').show()
        $('#contributorserror').hide();
    }); 
    $('#addneweditor input.addbutton').live('click', function()
    {
        $('#contributorserror').hide();
        var thisli = $(this).parents("li:first"); 
        var sdata = { roleuser:$('#addneweditor input:text').val(), newrole:'editor' }; 
        $.ajax({url:$("#admincontroleditors").val(), type: 'GET', data:sdata, success:function(result)
	        {
           
	            if (result.substring(0, 6) == "Failed") {
	                $('#contributorserror').text(result).show(300);
	            } else {
	                reload_scraper_contributors(); 
	                $('#addneweditor span').hide(); 
	                $('#addneweditor a').show(); 
	            }
	        },
	        error:function(jq, textStatus, errorThrown)
	        {
	            $('#contributorserror').text("Connection failed: " + textStatus + " " + errorThrown).show(300);
	        }
        }); 
    }); 

    $('.detachbutton').live('click', function() 
    {
        $('#contributorserror').hide();
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'' }; 
		changeRoles( sdata, '/dashboard/' );
    }); 

    $('.demotebutton').live('click', function() 
    {
        $('#contributorserror').hide();
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'' }; 
		changeRoles( sdata );
    }); 
    $('.promotebutton').live('click', function() 
    {
        $('#contributorserror').hide();
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'editor' }; 
		changeRoles( sdata );
    }); 


    if ($('#addneweditor input:text').length)
        $('#addneweditor input:text').autocomplete(
    {
        minLength: 2,
        open: function() {  $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" ); }, 
        close: function() {  $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" ); }, 
        //select: function(event, ui) { rewriteapiurl(); },
        source: function(request, response) 
        {
            var nolist = [ ]; 
            $("ul#contributorslist li span").each(function(i, el) { nolist.push($(el).text()); }); 
            $.ajax(
            {
                url: $('#id_api_base').val()+"scraper/usersearch",
                dataType: "jsonp",
                data: { format:"jsondict", maxrows:12, searchquery:request.term, nolist:nolist.join(" ") },
                success: function(data) 
                {
                    response($.map(data, function(item) { return  { label: item.username, desc: item.profilename, value: item.username }})); 
                }
            })
        },
        focus: function(event, ui)  { $( "#addneweditor input:text" ).val(ui.item.label);  return false; }
    })
    .data( "autocomplete" )._renderItem = function(ul, item) 
    {
        return $( "<li></li>" )
        .data( "item.autocomplete", item )
        .append( '<a><strong>' + item.desc + '</strong><br/><span>' + item.label + '</span></a>' )
        .appendTo(ul);
    };


    // Changing between public / protected(visible) / private

    $('#hide_privacy_choices').live('click', function() 
    {
        $('#privacy_status form').hide();
        $('#privacy_status>p, #show_privacy_choices').show();
    });

}
    
function setupChangeAttachables(short_name)
{
    // adding and removing attachables
    $('#addnewattachable a').click(function()
    {
        $('#addnewattachable a').hide()
        $('#addnewattachable span').show(); 
        $('attachableserror').hide();
    }); 
    $('#addnewattachable input.cancelbutton').click(function()
    {
        $('#addnewattachable span').hide(); 
        $('#addnewattachable a').show()
        $('attachableserror').hide();
    }); 
    $('#addnewattachable input.addbutton').click(function()
    {
        $('#attachablesserror').hide();
        var sdata = { attachable:$('#addnewattachable input:text').val(), action:'add' }; 
        $.ajax({url:$("#admincontrolattachables").val(), type: 'POST', data:sdata, success:function(result)
        {
           
            if (result.substring(0, 6) == "Failed") {
                $('#attachableserror').text(result).show(300);
            } else {
                reload_scraper_attachables(); 
                $('#addnewattachable span').hide(); 
                $('#addnewattachable a').show(); 
            }
        },
        error:function(jq, textStatus, errorThrown)
        {
            $('#attachableserror').text("Connection failed: " + textStatus + " " + errorThrown).show(300); 
        }}); 
    }); 

    $('#databaseattachablelist .removebutton').click(function() 
    {
        $('#attachableserror').hide();
        var sdata = { attachable:$(this).parents("li:first").find("span").text(), action:'remove' }; 
        $.ajax({url:$("#admincontrolattachables").val(), type: 'POST', data:sdata, success:function(result)
        {
           
            if (result.substring(0, 6) == "Failed") {
                $('#attachableserror').text(result).show(300);
            } else {
                reload_scraper_attachables(); 
                $('#addnewattachable span').hide(); 
                $('#addnewattachable a').show(); 
            }
        },
        error:function(jq, textStatus, errorThrown)
        {
            $('#attachableserror').text("Connection failed: " + textStatus + " " + errorThrown).show(300); 
        }}); 
    }); 
    
    if ($('#addnewattachable input:text').length)
        $('#addnewattachable input:text').autocomplete(
    {
        minLength: 2,
        open: function() {  $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" ); }, 
        close: function() {  $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" ); }, 
        //select: function(event, ui) { rewriteapiurl(); },
        source: function(request, response) 
        {
            var nolist = [ short_name ]; 
            $("ul#databaseattachablelist li span").each(function(i, el) { nolist.push($(el).text()); }); 
            $.ajax(
            {
                url: $('#id_api_base').val()+"scraper/search",
                dataType: "jsonp",
                data: { format:"jsondict", maxrows: 12, searchquery: request.term, quietfields:'description', nolist:nolist.join(" ") },
                success: function(data) 
                {
                    response($.map(data, function(item) { return  { label: item.short_name, desc: item.title, value: item.short_name }})); 
                }
            })
        },
        focus: function(event, ui)  { $( "#detail #id_name" ).val(ui.item.label);  return false; }
    }) 
    .data( "autocomplete" )._renderItem = function(ul, item) 
    {
        return $( "<li></li>" )
        .data( "item.autocomplete", item )
        .append( '<a><strong>' + item.desc + '</strong><br/><span>' + item.label + '</span></a>' )
        .appendTo(ul);
    };
}

*/

function htmlEscape(str) {
    return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function setupCodeOverview(short_name){
    //about
    $('#divAboutScraper').editable('../admin/', {
             indicator : 'Saving...',
             tooltip   : 'Click to edit...',
             cancel    : 'Cancel',
             submit    : 'Save',
             type      : 'textarea',
             loadurl: '../raw_about_markup/',
             onblur: 'ignore',
             event: 'dblclick',
             submitdata : {short_name: short_name},
             placeholder: ''
         });

    $('a.editdescription').click(
        function(){
             $('#divAboutScraper').dblclick();
             var oHint = $('<div id="divMarkupHint" class="content_footer"><p><strong>You can use Textile markup to style the description:</strong></p><ul><li>*bold* / _italic_ / @code@</li><li>* Bulleted list item / # Numbered list item</li><li>"A link":http://www.data.gov.uk</li><li>h1. Big header / h2. Normal header</li></ul></div>');
             if ($('#divAboutScraper #divMarkupHint').length == 0)  // quick hack to avoid multiple copies of this till it's done properly with a hidden div
                 $('#divAboutScraper form').append(oHint);
             return false;
        }
    );

    //title
    $('#hCodeTitle').editable('admin/', {
			cssclass : 'editable',
			width : $('#hCodeTitle').width() + 30,
            indicator : 'Saving...',
            tooltip   : 'Double click to edit title',
            cancel    : 'Cancel',
            submit    : 'Save',
			before : function(value, settings){
				$('#aEditTitle').hide();
			},
			callback : function(value, settings){
				$('#aEditTitle').show();
			},
			onreset : function(value, settings){
				$('#aEditTitle').show();
			},
            onblur: 'ignore',
            event: 'dblclick',
            placeholder: '',             
            submitdata : {short_name: short_name}
         });
         
    $('#aEditTitle').bind('click', function(){
		$('#hCodeTitle').dblclick();
		return false;
    });

    // this is complex because editable div is not what you see (it's a comma separated field)
    $('#divEditTags').editable($("#adminsettagurl").val(), 
    {
        indicator : 'Saving...', tooltip:'Click to edit...', cancel:'Cancel', submit:'Save tags',
        onblur: 'ignore', event:'dblclick', placeholder:'',
        onedit: function() 
        {
            var tags = [ ]; 
            $("#divScraperTags ul.tags li a").each(function(i, el) { tags.push($(el).text()); }); 
            $(this).text(tags.join(", ")); 
        },
        onreset: function() { $('#divEditTagsControls').hide(); },
        callback: function(lis) 
        {
            $('#divScraperTags ul.tags').html(lis); 
            $('#divEditTagsControls').hide(); 
            $('#addtagmessage').css("display", ($("#divScraperTags ul.tags li a").length == 0 ? "block" : "none")); 
        }
    }); 
    $('#aEditTags,#aEditTagsFromEmpty').click(function()
    {
        $('#divEditTags').dblclick();
        $('#divEditTagsControls').show();
        return false;
    });
    $('#divEditTagsControls').hide();
    $('#addtagmessage').css("display", ($("#divScraperTags ul.tags li a").length == 0 ? "block" : "none")); 
}

function setupScraperOverview(short_name)
{
/*    $('.data_tab').click(function(){
        // do nothing if already selected
        if ($(this).hasClass('selected')) 
            return;
        
        // make tab selected
        $('.data_tab').removeClass('selected'); // all
        $(this).addClass('selected');
    
        // show and hide
        $('.data_content').hide(); // all
        var tab_content_name = $(this).attr('id').replace('data_tab', 'data_content');
        var tablename = $(this).find("span.tablename").text(); 
        $('#' + tab_content_name).show();
    
        $("#downloadcsvtable").show(); 
        $("#downloadcsvtable").attr("href", $('#id_api_base').val() + "datastore/sqlite?format=csv&name=" + short_name 
                                                + "&query=select+*+from+`"+encodeURI(tablename)+"`"+"&apikey="+$('#id_apikey').val()); 
    }); 
*/
    $('.sqlite_view_schema').click( function() 
    {
        $('#sqlite_schema').toggle(500); 
        $('.sqlite_view_schema').toggle(); 
    });
    
    $("#popupinteractivesqlite").click(function() 
    {
        var url = "{{settings.VIEW_URL}}{% url rpcexecute 'quickcheck_datastore' %}?src="+decodeURIComponent(short_name); 
        $.modal('<iframe width="100%" height="100%" src='+url+'></iframe>', 
        {
            overlayClose: true,
            containerCss: { borderColor:"#0ff", height:"80%", padding:0, width:"90%" }, 
            overlayCss: { cursor:"auto" }, 
            onShow: function() 
            {
                $('.simplemodal-wrap').css("overflow", "hidden"); 
                $('.simplemodal-wrap iframe').width($('.simplemodal-wrap').width()-2); 
                $('.simplemodal-wrap iframe').height($('.simplemodal-wrap').height()-2); 
            }
        }); 
    }); 

    $("#downloadcsvtable").hide(); 
    $('.sqlite_view_schema:last').hide(); 
    $('#sqlite_schema').hide(); 
    $('#data_tab_1').click();

  	//scheduler
	if ($('#spnRunInterval').length > 0) {
	  $('#spnRunInterval').editable('admin/', {
	           indicator : 'Saving...',
	           tooltip   : 'Click to edit...',
	           cancel    : 'Cancel',
	           submit    : 'Save',
	           onblur: 'ignore',
	           data   : $('#hidScheduleOptions').val().replace('PLACEHOLDER', $('#spnRunIntervalInner').attr('rawInterval')),
	           type   : 'select',
	           event: 'dblclick',
	           placeholder: '',
	           submitdata : {short_name: short_name}
	       });
	}

	$('#aEditSchedule').click(
	    function(){
	         sCurrent = $('#spnRunIntervalInner').html().trim();               
	         $('#spnRunInterval').dblclick();
	         $('#spnRunInterval select').val(sCurrent);
	         return false;
	    }
	);
}

function setup_collaboration_ui(){
	$('#privacy_status, #contributors').hide();
	$('#collaboration ul.buttons a').bind('click', function(e){
		e.preventDefault();
		var href = $(this).attr('href');
		if($(href).is(':visible')){
			$('#privacy_status, #contributors').hide();
			$(this).removeClass('selected');
		} else {
			$(href).show().siblings('#privacy_status, #contributors').hide();
			$(this).addClass('selected').parent().siblings().children('a').removeClass('selected');
		}
		$('#privacy_status form').hide();
		$('#contributors .new_user_li, #contributors .error').remove();
		$('#privacy_status>p, #privacy_status>h4, #show_privacy_choices, #contributors a.add_user').show();
	});
	
	$('#show_privacy_choices').bind('click', function(){
        $('#privacy_status form').show();
        $('#privacy_status>p, #privacy_status>h4, #show_privacy_choices').hide();
    });

    $('#saveprivacy').bind('click', function(){
		$('input[name=privacy_status]:checked').hide().after('<img src="/media/images/load2.gif" width="16" height="16">').parents('tr').find('input, select').attr('disabled', true);
		if($('#current_vault_id').length){
			$.getJSON('/vaults/' + $('#current_vault_id').val() + '/removescraper/' + $('#scrapershortname').val() + '/' + $('input[name=privacy_status]:checked').val(), function(data) {
				if(data.status == 'ok'){
					reload_collaboration_ui('#privacy_status');
				} else {
					alert('Scraper could not be removed from vault: ' + data.error);
				}
			});
		} else {
			var sdata = { value: $('input[name=privacy_status]:checked').val() }
			$.ajax({url:$("#adminprivacystatusurl").val(), type: 'POST', data:sdata, success:function(result){
				if (result.substring(0, 6) == "Failed"){
	                alert(result); 
	            } else {
					console.log('success');
					reload_collaboration_ui('#privacy_status');
				}
			}});
		}
    }).hide();

	//	Handle clicks on the "make this public" and "make this protected" paragraphs
	$('#privacy_public, #privacy_protected').bind('change', function(){
		$('#saveprivacy').trigger('click');
	});
	
	$('#move_to_vault').bind('change', function(){
		if($(this).val() == ''){
			$(this).next().attr('disabled','disabled');
		} else {
			$(this).next().attr('disabled',false);
			$(this).parents('td').prev().find('input:radio').attr('checked', true)
		}
		console.log($(this).val());
	}).next().attr('disabled','disabled').bind('click', function(e){
		e.preventDefault();
		if($(this).is(':disabled')){
			// do nothing
			console.log('naughty');
		} else {
			$(this).val('Moving\u2026').attr('disabled','disabled').prev().attr('disabled','disabled');
			$(this).parents('td').prev().find('input:radio').hide().after('<img src="/media/images/load2.gif" width="16" height="16">').parents('tr').find('input, select').attr('disabled', true);
			$.getJSON($(this).prev().val(), function(data) {
				if(data.status == 'ok'){
					reload_collaboration_ui('#privacy_status');
				} else {
					alert('Scraper could not be moved to vault: ' + data.error);
				}
			});
		}
	});
	
	$('#collaboration a.add_user').bind('click', function(){
		var input = $('<input>').attr('id','username').attr('type','text').attr('class','text').bind('keydown', function(e){
			// handle Enter/Return key as a click on the Add button
			if((e.keyCode || e.which) == 13){
				$(this).next('a').trigger('click');
			}
		}).autocomplete({
			minLength: 2,
			source: function( request, response ) {
				$.ajax({
					url: $('#id_api_base').val() + "scraper/usersearch",
					dataType: "jsonp",
					data: {
						format:"jsondict", 
						maxrows:10, 
						searchquery:request.term
					},
					success: function( data ) {
						response( $.map( data, function( item ) {
							return {
								label: item.profilename + ' (' + item.username + ')',
								value: item.username
							}
						}));
					}
				});
			},
			select: function( event, ui ) {
				//  submit the name
				//  $(this).next('a').trigger('click');
			}
		});
	
		var confirm = $('<a>').text('Add!').bind('click', function(){			
			var $u = $(this).prev();
			$u.parents('ul').children('.error').slideUp(150);
			$('#collaboration .buttons li:eq(1) a').prepend('<img src="/media/images/load2.gif" width="16" height="16">');
			var sdata = { roleuser: $u.val(), newrole:'editor' }; 
	        $.ajax({
				url:$("#admincontroleditors").val(), 
				type: 'GET', 
				data:sdata, 
				success:function(result){
		            if (result.substring(0, 6) == "Failed") {
						$('#collaboration .buttons li:eq(1) img').remove();
		                $u.autocomplete("close").parents('ul').append('<li class="error">' + result + '</li>');
		            } else {
						reload_collaboration_ui('#contributors');
		            }
		        },
		        error:function(jq, textStatus, errorThrown)
		        {
					$('#collaboration .buttons li:eq(1) img').remove();
		            $u.autocomplete("close").parents('ul').append('<li class="error">Connection failed: ' + textStatus + ' ' + errorThrown + '</li>');
		        }
	        });
		});
		
		var li = $('<li>').hide().addClass("new_user_li").append('<label for="username">Username:</label>').append(input).append(confirm);
		
		$(this).slideUp(250).prev().append(li).children(':last').slideDown(250).find('#username').focus();
	
	});
	
	$('.demotelink').bind('click', function(){
		$(this).parents('ul').children('.error').slideUp(150);
		$('#collaboration .buttons li:eq(1) a').prepend('<img src="/media/images/load2.gif" width="16" height="16">');
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'' }; 
		$.ajax({
			url:$("#admincontroleditors").val(), 
			type: 'GET', 
			data:sdata, 
			success:function(result){
	            if (result.substring(0, 6) == "Failed") {
					$('#collaboration .buttons li:eq(1) img').remove();
	                $u.autocomplete("close").parents('ul').append('<li class="error">' + result + '</li>');
	            } else {
					reload_collaboration_ui('#contributors');
	            }
	        },
	        error:function(jq, textStatus, errorThrown)
	        {
				$('#collaboration .buttons li:eq(1) img').remove();
	            $u.autocomplete("close").parents('ul').append('<li class="error">Connection failed: ' + textStatus + ' ' + errorThrown + '</li>');
	        }
        });
    });
	
}

function reload_collaboration_ui(auto_enable_tab){

	$("#collaboration").load(document.location + ' #collaboration>*', function(response, status, xhr){
		if (status == "error") {
			alert('There was an error refreshing the collaboration UI: ' + xhr.status + " " + xhr.statusText);
		} else {
			$("#header_inner p").load(document.location + ' #header_inner p>*', function(response, status, xhr){
				if (status == "error") {
					alert('There was an error refreshing the collaboration UI: ' + xhr.status + " " + xhr.statusText);
				}
			});
			setup_collaboration_ui();
			if(auto_enable_tab){
				$(auto_enable_tab).show();
				$('ul.buttons li').eq($(auto_enable_tab).index() - 1).children().addClass('selected');
				console.log(auto_enable_tab + ' ' + $(auto_enable_tab).index());
			}
		}
	});
	
}

$(function(){
		
	$('li.viewsource a').bind('click', function(e){
		e.preventDefault();
		var url = $(this).attr('href');
		$.get(url, function(data){
	        $.modal('<pre id="viewsource">' + htmlEscape(data) + '</pre>', {
	            overlayClose: true, 
	            autoResize: true,
	            overlayCss: { cursor:"auto" },
				onShow: function(dialog){
					/* should this go in onOpen? */
					dialog.data.find('pre').snippet($('span.language').attr('rel'), {style:"vim", clipboard: "/media/js/ZeroClipboard.swf"});
				},
				onOpen: function(dialog) {
					dialog.data.show();
					dialog.overlay.fadeIn(200);
					dialog.container.fadeIn(200);
				},
				onClose: function(dialog) {
					dialog.container.fadeOut(200);
					dialog.overlay.fadeOut(200, function(){
						$.modal.close();
					});
				}
	        });
	    });
	});
	
	$("#download_table_csv a").attr("href", $('#id_api_base').val() + "datastore/sqlite?format=csv&name=" + $('#scrapershortname').val() + "&query=select+*+from+`"+ encodeURI( $(".data_tab:first .tablename").text() ) + "`" + "&apikey=" + $('#id_apikey').val());
	
	$('ul.data_tabs li').bind('click', function(){
		var eq = $(this).index();
		if($(this).is('#more_tabs li')){
			eq += $('#more_tabs').prevAll().length + 1;
			$(this).addClass('selected');
			$('#more_tabs').addClass('selected');
			$('.data_tabs .selected').not($(this)).not('#more_tabs').removeClass('selected');
		} else {
			$(this).addClass('selected');
			$('.data_tabs .selected').not($(this)).removeClass('selected');
		}
		$('.datapreview:eq(' + eq + ')').css({position:'static'});
		$('.datapreview').not(':eq(' + eq + ')').css({position:'absolute',left: '-9000px'});
        $("#download_table_csv").attr("href", $('#id_api_base').val() + "datastore/sqlite?format=csv&name=" + $('#scrapershortname').val() + "&query=select+*+from+`"+ encodeURI( $(".data_tab.selected .tablename").text() ) + "`" + "&apikey=" + $('#id_apikey').val());
	});
	
	$('ul.data_tabs li').each(function(){
		$(this).attr('title', $(this).index() );
	});


	function make_more_link(){
        $('ul.data_tabs .clear').before(
            $('<li id="more_tabs" title="Show more tabs" style="display:none"><span id="more_tabs_number">0</span> more &raquo;<ul></ul></li>')
        );
    }

    function update_more_link(int){
        $('#more_tabs').show().find('#more_tabs_number').text(int);
    }

    make_more_link();

	var table_width = 748;
    var tabs_width = 0;
    var more_link_width = $('#more_tabs').outerWidth() + 10;
    var hidden_tabs = 0;

	$('.data_tab').not('#more_tabs, #more_tabs li').each(function(){
		tabs_width += $(this).outerWidth(true);
		if(tabs_width > table_width - more_link_width){
			$(this).appendTo('#more_tabs ul');
			hidden_tabs++;
            update_more_link(hidden_tabs);
		}
	});
	
	$('.edit_schedule').bind('click', function(e){
		e.preventDefault();
		if($('#edit_schedule').is(':hidden')){
			$('#edit_schedule').show().prev().hide();
		} else {
			$('#edit_schedule').hide().prev().show();
		}
	});
	
	setup_collaboration_ui();
	
});





