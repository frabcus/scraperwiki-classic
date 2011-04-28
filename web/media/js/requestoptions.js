$(function()
{ 
	function requestOption($a){
		
		function requestOptionInner($a){
			$d = $a.parent().next();
			id = $d.attr('id');
			$a.addClass('selected').parent().next().css('border-color', '#39c').slideDown(250);
			$('#request_options h3 a.selected').not($a).removeClass('selected');
			$('#request_options div:visible').not($d).css('border-color', '#E8F2F9').slideUp(250);
			if(id == 'private'){
				show = '.urls, .columns, .frequency, .due_date, .name, .email';
			} else if(id == 'viz'){
				show = '.urls, .columns, .frequency, .due_date, .visualisation, .name, .email, .telephone';
			} else if(id == 'app'){
				show = '.urls, .columns, .frequency, .due_date, .application, .name, .email';
			} else if(id == 'etl'){
				show = '.description, .name, .email, .telephone, .company_name';
			} else {
				show = '.urls, .columns, .frequency, .due_date, .name, .email, .broadcast';
			}
			$(show, $('#request_form')).filter(':hidden').slideDown(250);
			$('#request_form li').not(show).slideUp(250);

            $('#id_category').val(id);
		}
		
		if($('#request_intro').is(':visible')){
			$('#request_intro:visible').fadeOut(200, function(){
				$('#request_form:hidden').fadeIn(200, function(){
					requestOptionInner($a)
				});
			});	
		} else {
			requestOptionInner($a)
		}
		
	}
		
	$('#request_options h3 a').bind('click', function(e){
		e.preventDefault();
		requestOption($(this));
	}).each(function(){
		h = $(this).outerHeight() - 2;
		$('<span>').addClass('arrow').css('border-width', Math.round(h/2) + 'px 10px ' + Math.round(h/2) + 'px 0px').attr('title',h).appendTo($(this));
	});

    // If the form is being returned with errors then the category will be set
    // so display the form as required by the selected category
    var choice = $('#id_category').val();
    if(choice !== ''){
        $('#request_options h3 a[href="#' + choice + '"]').click();
    }
	
	$('#id_due_date').datepicker({
		minDate: '+1'
	}).next().bind('click', function(){
		$(this).prev().datepicker("show");
	});
	
	$('body.tags .content #filter').css('visibility','hidden').bind('click', function(){
		if($('#filter_text').val() != ''){
			$('.content li').hide().filter(":contains(" + $('#filter_text').val() + ")").show();
			$(this).siblings('#reset').css('visibility','visible');
		}
	}).siblings('#reset').css('visibility','hidden').bind('click', function(){
		$('.content li').show();
		$(this).css('visibility','hidden');
		$('#filter_text').val('');
		$('#filter').css('visibility','hidden');
	}).siblings('#filter_text').bind('keyup', function(e){
		if(e.which == 13){
			if($('#filter_text').val() != ''){
				$('.content li').hide().filter(":contains(" + $('#filter_text').val() + ")").show();
				$(this).siblings('BASIC#reset').css('visibility','visible');
			}
		} else if($(this).val() != ''){
			$('#filter').css('visibility','visible');
		} else {
			$('#filter').css('visibility','hidden');
			$('#reset').css('visibility','hidden');
			$('.content li').show();
		}
	});
})