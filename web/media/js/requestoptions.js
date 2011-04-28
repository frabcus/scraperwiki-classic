
$(function()
{ 
	function requestOption($a){
		
		function requestOptionInner($a){
			$d = $a.parent().next();
			var id = $d.attr('id');
			$a.addClass('selected').parent().next().css('border-color', '#39c').slideDown(250);
			$('#request_options h3 a.selected').not($a).removeClass('selected');
			$('#request_options div:visible').not($d).css('border-color', '#E8F2F9').slideUp(250);
			$(showinglookup[id], $('#request_form')).filter(':hidden').slideDown(250);
			$('#request_form li').not(showinglookup[id]).slideUp(250);
            $('#id_category').val(id);
            $('#id_category_title').val($a.text());

            // jsondict option only exists for sqlite selection (not available in piston)
            var jd = $("#id_format option[value='jsonlist']"); 
            jd.attr("disabled", (id == "sqlite" ? "" : "disabled")); 
            if ((id != "sqlite") && jd.attr("selected"))
                $("#id_format option[value='jsondict']").attr("selected", true); 
            setTimeout(rewriteapiurl, 400); 
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
				$(this).siblings('#reset').css('visibility','visible');
			}
		} else if($(this).val() != ''){
			$('#filter').css('visibility','visible');
		} else {
			$('#filter').css('visibility','hidden');
			$('#reset').css('visibility','hidden');
			$('.content li').show();
		}
	});

    function rewriteapiurl()
    {
        var surl = [ $('#id_api_base').val() ]; 
        surl.push($('#id_category_title').val().replace("scraperwiki.", "").replace(".", "/")); 
        surl.push("?"); 
        var ents = $('#request_form li').not(':hidden'); 
        var entdropdown = ents.find('select'); 
        surl.push(entdropdown.attr("name"), "=", entdropdown.val()); 
        for (var i = 0; i < ents.length; i++)
        {
            var ent = $(ents[i]).find("input"); 
            if ((ent.length == 1) && (ent.val().length != 0))
                surl.push("&", ent.attr("name"), "=", encodeURIComponent(ent.val())); 
        }
        $('#id_apiuri').val(surl.join("")); 
    }
    $('#request_form input, #request_form textarea').each(function() {$(this).keyup(rewriteapiurl)}); 
    $('#request_form select').each(function() {$(this).change(rewriteapiurl)}); 
}); 

