// Boilerplate to add CSRF protection headers, taken from https://docs.djangoproject.com/en/1.3/ref/contrib/csrf/
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function setupButtonConfirmation(sId, sMessage)
{
    $('#' + sId).click(
        function(){
            var bReturn = false;
            if (confirm(sMessage) == true){
                bReturn = true;
            }
            return bReturn
        }    
    );
	return false;
}

function setupSearchBoxHint()
{
    $('#divSidebarSearch input:text').focus(function() {
        if ($('#divSidebarSearch input:submit').attr('disabled')) {
            $(this).val('');
            $(this).removeClass('hint');
            $('#divSidebarSearch input:submit').removeAttr('disabled'); 
        }
    });
    $('#divSidebarSearch input:text').blur(function() {
        if(!$('#divSidebarSearch input:submit').attr('disabled') && ($(this).val() == '')) {
            $(this).val('Search');
            $(this).addClass('hint');
            $('#divSidebarSearch input:submit').attr('disabled', 'disabled'); 
        }
    });
    $('#divSidebarSearch input:text').blur();
}


function setupNavSearchBoxHint(){
    $('#navSearch input:text').focus(function() {
        if ($('#navSearch input:submit').attr('disabled')) {
            $(this).val('');
            $(this).removeClass('hint');
            $('#navSearch input:submit').removeAttr('disabled'); 
        }
		$('#navSearch').addClass('focus');
    });
    $('#navSearch input:text').blur(function() {
        if(!$('#navSearch input:submit').attr('disabled') && ($(this).val() == '')) {
            $(this).val('Search datasets');
            $(this).addClass('hint');
            $('#navSearch input:submit').attr('disabled', 'disabled'); 
        }
		$('#navSearch').removeClass('focus');
    });
    $('#navSearch input:text').blur();
}

function newCodeObject($a){
	if($a){	
		url = '/' + $a.data('wiki_type') + 's/new/choose_template/?ajax=1';
		if ( $a.data('sourcescraper') ) {
			url += "&sourcescraper=" + $a.data('sourcescraper');
		}
		
		/*	
			NOTE:
			This actually causes a problem, if someone tries to create a new View
			(with a sourcescraper attribute) and then ALSO tries to save it into
			a vault. They end up being taken to a url like:
			/views/new/php?sourcescraper=ORIGINAL_SCRAPER/tovault/VAULT_ID/?name=NEW_VIEW
			which doesn't work. The View isn't created in the vault. Instead, it's
			created publically, and the sourcescraper name is taken to be:
			"ORIGINAL_SCRAPER/tovault/VAULT_ID/?name=NEW_VIEW"
			D'oh!!
		*/
		
		$.get(url, function(data){
	        $.modal('<div id="template_popup">'+data+'</div>', {
	            overlayClose: true, 
	            autoResize: true,
	            overlayCss: { cursor:"auto" },
				onOpen: function(dialog) {
					dialog.data.show();
					dialog.overlay.fadeIn(200);
					dialog.container.fadeIn(200);
				},
				onShow: function(dialog){
					$('#simplemodal-container').css('height', 'auto');
					$('#chooser_vaults h2', dialog.data).bind('click', function(e){
						if($(this).next().is(':visible')){
							$(this).children('input').attr('checked', false);
							$(this).nextAll('p').slideUp(250);
						} else {
							$(this).children('input').attr('checked', true);
							$(this).nextAll('p').slideDown(250, function(){
								$('#chooser_name_box').focus();
							});
						}
					});
					if($a.data('vault_id')){
						$('#chooser_vaults h2', dialog.data).trigger('click');
						$('select option[value$="/' + $a.data('vault_id') + '/"]', dialog.data).attr('selected', 'selected');
					}
					$('li a', dialog.data).bind('click', function(e){
						if( ! $('#chooser_vaults h2 input').is(":visible")  ) {
							return;
						}

						if ( ! $('#chooser_vaults h2 input').is(":checked") ) {
							return;
						}

						e.preventDefault();
						if($('#chooser_vaults h2 input', dialog.data).is(':checked')){
							if($('#chooser_name_box', dialog.data).val() == ''){
								$('span.warning', dialog.data).remove();
								text = $('label', dialog.data).attr('title');
								$('p', dialog.data).eq(0).addClass('error').append('<span class="warning"><span></span>' + text + '</span>');
								$('#chooser_name_box', dialog.data).bind('keyup', function(){
									$('p.error', dialog.data).removeClass('error').children('span').remove();
									$(this).unbind('keyup');
								})
							} else {
								$(this).addClass('active');
								location.href = $('#chooser_vault').val().replace('/python/', '/' + $(this).attr('href').replace(/.*\//, '') + '/') + '?name=' + encodeURIComponent($('#chooser_name_box').val());
							}
						}
					});
				},
				onClose: function(dialog) {
					dialog.container.fadeOut(200);
					dialog.overlay.fadeOut(200, function(){
						$.modal.close();
					});
				}
	        });
	    });		
		
		
	} else {
		alert('no anchor element provided');
	}
}

function newUserMessage(url){
	
	if(url == undefined){
		alert('No message url specified');
	} else {
//    	if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Profile buttons', 'Send Message']); }
    	$.get(url, function(data){
	        $.modal('<div id="message_popup">'+data+'</div>', {
	            overlayClose: true, 
	            autoResize: true,
	            overlayCss: { cursor:"auto" },
				onOpen: function(dialog) {
					dialog.data.show();
					dialog.overlay.fadeIn(200);
					dialog.container.fadeIn(200);
				},
				onShow: function(dialog){
					$('#simplemodal-container').css('height', 'auto');
					$('h1', dialog.data).append(' to ' + $('.profilebio h3').text());
					$('textarea', dialog.data).focus();
					$(':submit', dialog.data).bind('click', function(e){
						e.preventDefault();
					//	var action = location.href + '/message/';
						var action = $('form', dialog.data).attr('action');
						var data = $('form', dialog.data).serialize();
						$.ajax({
							type: 'POST',
							url: action,
							data: data,
							success: function(data){
								if(data.status == 'ok'){
									if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Profile buttons', 'Send Message (message sent!)']); }
									$('h1', dialog.data).after('<p class="success">Message sent!</p>');
									$('form', dialog.data).remove();
									var t = setTimeout(function(){
										$('#simplemodal-overlay').trigger('click');
									}, 1000);
								} else {
									$('p.last', dialog.data).before('<p class="error">' + data.error + '</p>');
								}
							},
							dataType: 'json'
						});
					});
				},
				onClose: function(dialog) {
					dialog.container.fadeOut(200);
					dialog.overlay.fadeOut(200, function(){
						$.modal.close();
					});
				}
	        });
	    });
	}
}


$(function()
{
    setupSearchBoxHint();
    setupNavSearchBoxHint();

    $('a.editor_view, div.network .view a, a.editor_scraper, .add_to_vault a').click(function(e) {
		e.preventDefault();
		newCodeObject($(this));
    });
	
	function developer_show(){
		$('#intro_developer, #intro_requester, #blob_requester').fadeOut(500);
		$('#more_developer_div').fadeIn(500);
		$('#blob_developer').animate({left: 760}, 500, 'easeOutCubic').addClass('active');
	}
	
	function developer_hide(){
		$('#intro_developer, #intro_requester, #blob_requester').fadeIn(500);
		$('#more_developer_div').fadeOut(500);
		$('#blob_developer').animate({left: 310}, 500, 'easeOutCubic').removeClass('active');
	}
	
	function requester_show(){
		$('#intro_developer, #intro_requester, #blob_developer').fadeOut(500);
		$('#more_requester_div').fadeIn(500);
		$('#blob_requester').animate({left: 10}, 500, 'easeOutCubic').addClass('active');
	}
	
	function requester_hide(){
		$('#intro_developer, #intro_requester, #blob_developer').fadeIn(500);
		$('#more_requester_div').fadeOut(500);
		$('#blob_requester').animate({left: 460}, 500, 'easeOutCubic').removeClass('active');
	}
	
	$('#blob_developer').css('cursor', 'pointer').bind('click', function(e){
		e.preventDefault();
	    if($(this).is('.active')){
	        developer_hide();
	    } else {
	        developer_show();
			if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Homepage buttons', 'Developer - find out more']); }
	    }
	});
	
	$('#blob_requester').css('cursor', 'pointer').bind('click', function(e){
		e.preventDefault();
	    if($(this).is('.active')){
	        requester_hide();
	    } else {
	        requester_show();
			if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Homepage buttons', 'Requester - find out more']); }
	    }
	});
	
	$('#more_developer, #intro_developer').css('cursor', 'pointer').bind('click', function(e){
		e.preventDefault();
		developer_show();
		if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Homepage buttons', 'Developer - find out more']); }
	});

	$('#more_requester, #intro_requester').css('cursor', 'pointer').bind('click', function(e){
		e.preventDefault();
		requester_show();
		if (typeof _gaq !== 'undefined'){ _gaq.push(['_trackEvent', 'Homepage buttons', 'Requester - find out more']); }
	});

	$('#more_developer_div .back').bind('click', function(e){
		e.preventDefault();
		developer_hide();
	});	
	
	$('#more_requester_div .back').bind('click', function(e){
		e.preventDefault();
		requester_hide();
	});
	
	
	
	
	$('a.submit_link').each(function(){
		id = $(this).siblings(':submit').attr('id');
		$(this).addClass(id + '_link')
	}).bind('click', function(e){
		e.preventDefault();
		$(this).siblings(':submit').trigger('click');
	}).siblings(':submit').hide();
	
	$('#fourohfoursearch').val($('body').attr('class').replace("scrapers ", "").replace("views ", ""));
	
	
		
	
	$('div.vault_users_popover').each(function(i,el){
		//	This centres the Users Popover underneath the Users toolbar button
		var popo = $(this);
		var link = $(this).prevAll('.vault_users');
		var anchor = link.position().left + (0.5 * link.outerWidth());
		popo.css('left', anchor - (popo.outerWidth() / 2) );
	});
	
	$('body.vaults a.vault_users').bind('click', function(e){
		var $a = $(this).addClass('hover');
		var $p = $a.siblings('div.vault_users_popover');
		if($p.is(':visible')){
			$p.fadeOut(400, function(){
				$p.find('li.new_user_li, li.error').remove();
				$p.children('a.add_user').show();
			});
			$a.removeClass('hover');
			$('html').unbind('click');
		} else {
			$p.fadeIn(150);
			$('html').bind('click', function(e){
				if( $(e.target).parents().index($a) == -1 ) {
					if( $(e.target).parents().index($p) == -1 ) {
						if( $(e.target).parents().index($('.ui-autocomplete')) == -1 ) {
							if($(e.target).not('[class*="ui-"]').length){
								// they didn't click on the users link or the popover or the autocomplete
								$p.filter(':visible').fadeOut(400, function(){
									$p.find('li.new_user_li, li.error').remove();
									$p.find('a.add_user').show();
								});
								$a.removeClass('hover');
								$('html').unbind('click');
							}
						}
					}
				}
			});
		}
	});
	
	$('body.vaults a.add_user').bind('click', function(){
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
				//	submit the name
				//	$(this).next('a').trigger('click');
			}
		});
	
		var confirm = $('<a>').text('Add!').bind('click', function(){
			var closure = $(this).prev();
			closure.parents('ul').children('.error').slideUp(150);
			var username = closure.val();
			var vault_id = closure.parents('div').find('a.add_user').attr('rel');
			var url = '/vaults/' + vault_id + '/adduser/' + username + '/';
			$.getJSON(url, function(data) {
				if(data.status == 'ok'){
					closure.autocomplete("close").parents('ul').next('a').slideDown(150);
					closure.updateUserCount(1).parent().before( data.fragment ).remove();
				} else if(data.status == 'fail'){
					closure.autocomplete("close").parents('ul').append('<li class="error">' + data.error + '</li>');
				}
			});
		});
		var li = $('<li>').hide().addClass("new_user_li").append('<label for="username">Username:</label>').append(input).append(confirm);
		$(this).slideUp(250).prev().append(li).children(':last').slideDown(250).find('#username').focus();
	});
	
	$('body.vaults a.user_delete').live('click', function(e){
		e.preventDefault();
		var url = $(this).attr('href');
		var closure = $(this);
		$.ajax({
			url: url,
			dataType: 'json',
			success: function(data) {
				if(data.status == 'ok'){
					closure.updateUserCount(-1).parent().slideUp(function(){
						$(this).remove();
					});
				} else if(data.status == 'fail'){
					closure.parents('ul').append('<li class="error">Error: ' + data.error + '</li>');
				}
			}, 
			error: function(data){
				closure.parents('ul').append('<li class="error">There was an error loading the json delete action</li>');
			}
		});
	});
	
	jQuery.fn.updateUserCount = function(increment) {
		//	Must be called from an element within <div class="vault_header"></div>
		return this.each(function() {
		    var $el = $(this);
			var number_of_users = Number($el.parents('.vault_header').find('.vault_users_popover li').not('.new_user_li').length) + increment;
			if(number_of_users == 1){
				x_users = '1 member';
			} else {
				x_users = number_of_users + ' members';
			}
			$el.parents('.vault_header').find('.x_users').text(x_users);
		});
	}
	
	$('body.vaults .transfer_ownership a').bind('click', function(e){
		e.preventDefault();
		$(this).next('span').show().children(':text').focus();
		$('span', this).show();
	});
	
	$('body.vaults .transfer_ownership input:text').autocomplete({
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
			// submit the name
			$(this).next('input').attr('disabled',false);
		}
	}).next().bind('click', function(){
		var url = $(this).parent().prev().attr('href') + $(this).prev().val() + '/';
		var button = $(this).val('Transferring\u2026');
		$.ajax({
			url: url,
			dataType: 'json',
			success: function(data) {
				if(data.status == 'ok'){
					window.location.reload();
				} else if(data.status == 'fail'){
					button.after('<em class="error">Error: ' + data.error + '</em>');
					button.val('Transfer!');
				}
			}, 
			error: function(data){
				button.after('<em class="error">Error: ' + data.error + '</em>');
				button.val('Transfer!');
			}
		});
	}).attr('disabled', true);
	
	if($('#alert_outer').length){
		$('<a>').attr('id','alert_close').bind('click', function(){ 
			$('#alert_outer').slideUp(250);
			$('#nav_outer').animate({marginTop:0}, 250);
		}).appendTo('#alert_inner');
		$('#nav_outer').css('margin-top', $('#alert_outer').outerHeight());
	}
	
	$('#compose_user_message').bind('click', function(e){
		e.preventDefault();
		newUserMessage($(this).attr('href'));
	});
	
	if($('#compose_user_message').length && window.location.hash == '#message'){
		$('#compose_user_message').trigger('click');
	}
	
	
});



function setupScroller(){
    
    //left right buttons
    $('.scroller a.scroll_left').click(
        function(){
            scrollScroller('left')
            return false;
        }
    );
    $('.scroller a.scroll_right').click(
        function(){
            scrollScroller('right')
            return false;
        }
    );
    
    //resize
    $(window).resize(
        function(){
            var iNewWidth = $('.scroller .scroller_wrapper').width() / 2;
            if(iNewWidth < 250){
               iNewWidth = 250;
            }
            $('.scroller .scroll_item').width(iNewWidth);
        }
    );
}

function scrollScroller(sDirection){

    //can scroll?
    var bCanScroll = true;
    var iCurrentLeft = parseInt($('.scroller .scroll_items').css('left'));
    if(sDirection == 'left' && iCurrentLeft >= 0){
        bCanScroll = false;
    }

    if(bCanScroll == true){
        //get the width of one item
        iWidth = $('.scroller .scroll_items :first-child').outerWidth() + 18;
        sWidth = ''
        if(sDirection == 'right'){
            sWidth = '-=' + iWidth
        }else{
            sWidth = '+=' + iWidth        
        }

        //scroll   
        $('.scroller .scroll_items').animate({
          left: sWidth
        }, 500);
    }
    
}

function setupIntroSlideshow(){
    $('.slide_show').cycle({
		fx: 'fade',
        speed:   1000, 
        timeout: 7000, 
        next:   '.slide_show', 
        pause:   1,
        pager: '.slide_nav',
        autostop: 0
	});
}


function setupCKANLink(){
    $.ajax({
        url:'http://ckan.net/api/search/resource',
        dataType:'jsonp',
        cache: true,
        data: {url: 'scraperwiki.com', all_fields: 1},
        success:function(data){
            var id = window.location.pathname.split('/')[3];
            $.each(data.results, function(index,ckan){
                if ($.inArray(id, ckan.url.split('/')) != -1){
                    $('div dl').append('<dt>CKAN:</dt><dd><a href="http://ckan.net/package/'+ckan.package_id+'" target="_blank">link</a><dd>');
                }
            });
        }
    });
}

function optiontojson(seloptsid, currsel)
{
    var result = { };
    $(seloptsid+" option").each(function(i, el) 
    {
        result[$(el).attr("value")] = $(el).text() 
        if ($(el).text() == currsel)
            result["selected"] = $(el).attr("value"); 
    }); 
    return $.toJSON(result); 
}

