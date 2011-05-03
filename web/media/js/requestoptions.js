
$(function()
{ 
	function requestOption($a){
		
		function requestOptionInner($a){
			$d = $a.parent().next();
			var id = $d.attr('id');
            window.location.hash = id; 
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

    if (window.location.hash)
        setTimeout(function() { $('#request_options div'+window.location.hash).prev().find("a").click(); }, 200); 


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
            var ent = $(ents[i]).find("input, textarea"); 
            if ((ent.length == 1) && (ent.val().length != 0))
                surl.push("&", ent.attr("name"), "=", encodeURIComponent(ent.val())); 
        }
        $('#id_apiuri').val(surl.join("")); 
    }
    $('#request_form input, #request_form textarea').each(function() 
    {   
        $(this).keypress(function(e)
        {
            if (e.which == 13)
                {  $("#btnCallMethod").click();  e.preventDefault();  return false }
        })
        $(this).keyup(rewriteapiurl); 
    }); 
    $('#request_form select').each(function() { $(this).change(rewriteapiurl) }); 

    var autocompletedata = 
    {
        minLength: 2,
        open: function() {  $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" ); }, 
        close: function() {  $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" ); rewriteapiurl(); }, 
        select: function(event, ui) { rewriteapiurl(); },
        source: function(request, response) 
        {
            $.ajax(
            {
                url: $('#id_api_base').val()+"scraper/search",
                dataType: "jsonp",
                data: { format:"jsondict", maxrows: 12, searchquery: request.term },
                success: function(data) 
                {
                    response($.map(data, function(item) { return  { label: item.short_name, desc: item.title, value: item.short_name }})); 
                }
            })
        }
    }; 
    $('#request_form #id_attach').autocomplete(autocompletedata); 
        // reuse the same settings with one extra function (it's been verified that the settings are copied over internally)
    autocompletedata.focus = function(event, ui)  { $( "#request_form #id_name" ).val(ui.item.label);  return false; }; 
    $('#request_form #id_name').autocomplete(autocompletedata)
    .data( "autocomplete" )._renderItem = function(ul, item) 
    {
        return $( "<li></li>" )
        .data( "item.autocomplete", item )
        .append( "<a><b>" + item.label + "</b><br>" + item.desc + "</a>" )
        .appendTo(ul);
    };

    $('#request_form #id_quietfields').autocomplete({source: [ "", "code", "userroles", "runevents", "datasummary" ]}); 

    var scraperlistcall = null; 
    $('#request_form #id_name').bind('keyup change', function()
    {
        if (scraperlistcall != null)
            clearTimeout(scraperlistcall); 
        $('#listtables').html("<li>Waiting...</li>"); 
        scraperlistcall = setTimeout(function()
        {
            scraperlistcall = null; 
            var aName = $('#request_form #id_name').val();
            $('#listtables').html("<li>Loading...</li>"); 
            $.ajax({url:$('#id_api_base').val()+"scraper/getinfo", dataType:"jsonp", data:{name:aName, quietfields:"code|runevents|userroles"}, error: function(jq, status) { alert(status); }, success:function(v) 
            { 
                $('#listtables').empty(); 
                if (v && v[0] && v[0].datasummary && v[0].datasummary.tables)
                {
                    for (var tablename in v[0].datasummary.tables)
                    {
                        var table = v[0].datasummary.tables[tablename]; 
                        $('#listtables').append('<li><b>'+tablename+'</b> ['+table.count+'] '+table.sql+'</li>'); 
                    }
                    $('#listtables li').click(function() 
                    {
                        $('#tablename').val($(this).find("b").text()); 
                        $('#query').val("select * from "+$(this).find("b").text()+" limit 10"); 
                    }); 
                }
                else if (v && v.error)
                    $('#listtables').html("<li>"+v.error+"</li>"); 
                else
                    $('#listtables').html("<li>No tables</li>"); 
            }}); 
        }, 500); 
    }); 
}); 
