/* GENERAL FUNCTIONS */

$.fn.digits = function(){
    return this.each(function(){
        $(this).text( $(this).text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,") );
    })
}

$.extend({
    keys: function(obj){
		// Usage:
		// var obj = {a: 1, b: 2, c: 3, d: 4, kitty: 'cat'}
		// alert($.keys(obj));    ->   a,b,c,d,kitty
        var a = [];
        $.each(obj, function(k){ a.push(k) });
        return a;
    }
})

function pluralise(thing,number,plural){
	if(plural == null){ plural = thing + 's'; }
    return (number == 1 ? thing : plural);
}

function htmlEscape(str){
    return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function safeString(str){
    return str.replace(/[^a-zA-Z0-9]+/g, '_').replace(/(^_|_$)/g, '');
}




/* SETUP FUNCTIONS */

function setupCodeOverview(short_name){
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
}

function setupCollaborationUI(){
	$('#privacy_status, #contributors').hide();
	$('#collaboration ul.buttons a, #header .privacystatus').bind('click', function(e){
		e.preventDefault();
		var href = $(this).attr('href');
		if($(href).is(':visible')){
			$('#privacy_status, #contributors').hide();
			$('#collaboration ul.buttons a[href="' + href + '"]').removeClass('selected');
		} else {
			$(href).show().siblings('#privacy_status, #contributors').hide();
			$('#collaboration ul.buttons a[href="' + href + '"]').addClass('selected').parent().siblings().children('a').removeClass('selected');
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
					reloadCollaborationUI('#privacy_status');
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
					reloadCollaborationUI('#privacy_status');
				}
			}});
		}
    }).hide();

	//	Handle clicks on the "make this public" and "make this protected" paragraphs
	$('#privacy_public, #privacy_protected, #privacy_private').bind('change', function(){
		$('#saveprivacy').trigger('click');
	});

	$('#move_to_vault').bind('change', function(){
		if($(this).val() == ''){
			$(this).next().attr('disabled','disabled');
		} else {
			$(this).next().attr('disabled',false);
			$(this).parents('td').prev().find('input:radio').attr('checked', true)
		}
	}).next().attr('disabled','disabled').bind('click', function(e){
		e.preventDefault();
		if(!$(this).is(':disabled')){
			$(this).val('Moving\u2026').attr('disabled','disabled').prev().attr('disabled','disabled');
			$(this).parents('td').prev().find('input:radio').hide().after('<img src="/media/images/load2.gif" width="16" height="16">').parents('tr').find('input, select').attr('disabled', true);
			$.getJSON($(this).prev().val(), function(data) {
				if(data.status == 'ok'){
					reloadCollaborationUI('#privacy_status');
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
						reloadCollaborationUI('#contributors');
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
					reloadCollaborationUI('#contributors');
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

function reloadCollaborationUI(auto_enable_tab){
	$("#collaboration").load(document.location + ' #collaboration>*', function(response, status, xhr){
		if (status == "error") {
			alert('There was an error refreshing the collaboration UI: ' + xhr.status + " " + xhr.statusText);
		} else {
			$("#header p").load(document.location + ' #header p>*', function(response, status, xhr){
				if (status == "error") {
					alert('There was an error refreshing the collaboration UI: ' + xhr.status + " " + xhr.statusText);
				}
			});
			setupCollaborationUI();
			if(auto_enable_tab){
				$(auto_enable_tab).show();
				$('ul.buttons li').eq($(auto_enable_tab).index() - 1).children().addClass('selected');
			}
		}
	});
}

function setupScheduleUI(){
	$('#edit_schedule input').bind('change', function(){
		if($(this).is(':disabled')){
			alert('That button is disabled');
		} else {
			$.getJSON($(this).val(), function(data) {
				if(data.status == 'ok'){
					reloadScheduleUI();
				} else {
					alert('New schedule could not be saved: ' + data.error);
				}
			});
		}
	});

	$('.edit_schedule').bind('click', function(e){
		e.preventDefault();
		if($('#edit_schedule').is(':hidden')){
			$('#edit_schedule').show().prev().hide();
			$(this).addClass('cancel').text('Cancel');
		} else {
			$('#edit_schedule').hide().prev().show();
			$(this).removeClass('cancel').text('Edit');
		}
	});

	$('.schedule a.run').bind('click', function(e){
		e.preventDefault();
		$.getJSON($(this).attr('href'), function(data) {
			if(data.status == 'ok'){
				reloadScheduleUI();
			} else {
				alert('Could not run scraper: ' + data.error);
			}
		});
	});
}

function reloadScheduleUI(){
	$("td.schedule").load(document.location + ' td.schedule>*', function(response, status, xhr){
		if (status == "error") {
			alert('There was an error refreshing the schedule UI: ' + xhr.status + " " + xhr.statusText);
		} else {
			setupScheduleUI();
		}
	});
}




/* ONREADY FUNCTIONS */

$(function(){
    // globals
    api_url = $('#id_api_base').val();
	sqlite_url = api_url + 'datastore/sqlite?'
	if($('#id_apikey').val() != ''){
		apikey = $('#id_apikey').val();
		sqlite_url += 'apikey=' + apikey + '&';
	} else {
		apikey = null;
	}
    short_name = $('#scrapershortname').val();
    data_tables = [];

    setupDataPreviews();
	setupCollaborationUI();
	setupScheduleUI();

	$('li.share .embed a').bind('click', function(e){
		e.preventDefault();
		$(this).parents('.share_popover').fadeOut(400).prev().removeClass('hover');
		$('html').unbind('click');
        $('#add_view_to_site').modal({
            overlayClose: true,
            autoResize: true,
            overlayCss: { cursor:"auto" },
			onShow: function(dialog){
				$('#simplemodal-container').css('height', 'auto');
				$("pre", dialog.data).snippet('html', {style:"vim", clipboard: "/media/js/ZeroClipboard.swf"});
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

	$('li.share a, li.admin a').each(function(){
		$(this).bind('click', function(){
			var $a = $(this).addClass('hover');
			var $p = $a.siblings('div');
			if($p.is(':visible')){
				$p.fadeOut(400);
				$a.removeClass('hover');
				$('html').unbind('click');
			} else {
				$p.fadeIn(150, function(){
					$('html').bind('click', function(e){
						if( $(e.target).parents().index($a.parent()) == -1 ) {
							if( $(e.target).parents().index($p) == -1 ) {
								$p.filter(':visible').fadeOut(400);
								$a.removeClass('hover');
								$('html').unbind('click');
							}
						}
					});
				});
			}
		});
	});

	$('#delete_scraper, #empty_datastore').bind('click', function(e){
		e.preventDefault();
		$(this).next().children(':submit').trigger('click');
	});

	function show_new_tag_box(){
		$('div.tags').show();
		$('.new_tag').hide().next().show().find('input').focus();
	}

	function hide_new_tag_box(){
		$('li.new_tag_box input').animate({width:1}, 200, function(){
			$(this).css('width','auto').val('').parent().hide().prev().show();
			if( ! $('div.tags li').not('.new_tag, .new_tag_box').length ){
				$('div.tags').fadeOut();
			}
		});
	}

	$('.new_tag a, div.network .titlebar .tag a').bind('click', function(e){
		e.preventDefault();
		show_new_tag_box();
	});

	$('li.new_tag_box input').bind('keyup', function(event){
		var key = event.keyCode ? event.keyCode : event.which ? event.which : event.charCode;
		if(key == 13){
			var new_tag = $(this).val();
			var new_tag_array = new_tag.split(',');
			var tags = [ ];
	        $("div.tags ul li").not('.new_tag, .new_tag_box').each(function(i, el) {
				tags.push($(el).children('a:first').text());
			});
			tags.push(new_tag);
			$.ajax({
				type: 'POST',
				url: $("#adminsettagurl").val(),
				data: {value: tags.join(",") + ','},
				success: function(data){
					var new_html = '';
					$.each(new_tag_array, function(i, t){
						new_html += '<li class="editable"><a href="/tags/' + encodeURIComponent(trim(t)) + '">' + trim(t) + '</a><a class="remove" title="Remove this tag">&times;</a></li>';
					});
					$('li.new_tag_box input').val('').parent().prev().before(new_html);
				}, error: function(){
					alert('Sorry, your tag could not be added. Please try again later.');
				},
				dataType: 'html',
				cache: false
			});
		}
	}).bind('focus', function(){
		if(typeof(new_tag_hider) != 'undefined'){ clearTimeout(new_tag_hider); }
		$(this).parent().addClass('focus');
	}).bind('blur', function(){
		new_tag_hider = setTimeout(function(){hide_new_tag_box();}, 1000);
		$(this).parent().removeClass('focus');
	}).next('.hide').bind('click', function(){
		hide_new_tag_box();
	});

	$('div.tags a.remove').live('click', function(e){
		e.preventDefault();
		$old_tag = $(this).parent();
		var tags = [ ];
        $("div.tags ul li").not('.new_tag, .new_tag_box').not($old_tag).each(function(i, el) {
			tags.push($(el).children('a:first').text());
		});

		$.ajax({
			type: 'POST',
			url: $("#adminsettagurl").val(),
			data: {value: tags.join(", ")},
			success: function(data){
				$old_tag.remove();
				if( ! $('div.tags li').not('.new_tag, .new_tag_box').length ){
					$('div.tags').fadeOut();
				}
			}, error: function(){
				alert('Sorry, your tag could not be removed. Please try again later.');
			},
			dataType: 'html',
			cache: false
		});
	});
});

function setupTabFolding(){

  function make_more_link(){
    $('ul.data_tabs .clear').before(
      $('<li id="more_tabs" title="Show more tabs" style="display:none"><span id="more_tabs_number">0</span> more &raquo;<ul></ul></li>')
    )
  }

  function update_more_link(int){
    $('#more_tabs').show().find('#more_tabs_number').text(int)
  }

  make_more_link()

  var table_width = 900;
  var tabs_width = 0;
  var more_link_width = $('#more_tabs').outerWidth() + 10;
  var hidden_tabs = 0;

  $('.data_tab').not('#more_tabs, #more_tabs li').each(function(){
    tabs_width += $(this).outerWidth(true)
    if(tabs_width > table_width - more_link_width){
      $(this).appendTo('#more_tabs ul')
      hidden_tabs++
      update_more_link(hidden_tabs)
    }
  })
}

$.fn.switchTab = function(){
  return this.each(function(){
    $('.data_tab.selected').removeClass('selected');
    $(this).addClass('selected');

    if($(this).is('#more_tabs li')){
      $('#more_tabs').addClass('selected');
    } else {
      $('#more_tabs').removeClass('selected');
    }

    var table_name = $(this).attr('id').replace('data_tab_', '');
    var $dp_div = $('#data_preview_'+table_name);

    $dp_div.removeClass('hidden').siblings().addClass('hidden');
  })
}

function setupDataPreviews() {
  setupTabFolding()
  $('li.data_tab').live('click', function(){
    $(this).switchTab()
  })
  $('div.datapreview table').dataTable({
    "bJQueryUI": true,
    "sPaginationType": "full_numbers",
    "sScrollX": "100%",
    "bStateSave": true,
    "bScrollCollapse": true,
    "sDom": '<"H"lfrp>t',
    "fnRowCallback": function( tr, array, iDisplayIndex, iDisplayIndexFull ) {
      $('td', tr).each(function(){
        $(this).html(
          $(this).html().replace(
          /((http|https|ftp):\/\/[a-zA-Z0-9-_~#:\.\?%&\/\[\]@\!\$'\(\)\*\+,;=]+)/g,
          '<a href="$1">$1</a>'
          )
        );
      });
      return tr;
    }
  })
  $('li.data_tab').eq(0).switchTab()
}
