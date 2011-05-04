

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


function newCodeObject(wiki_type)
{
    url = '/' + wiki_type + 's/new/choose_template/?ajax=1';
    //if (scraper_short_name != '')
    //    url += '&sourcescraper=' + scraper_short_name; 
    
    $.get(url, function(data) 
    {
        $.modal('<div id="template_popup">'+data+'</div>', 
        {
            overlayClose: true, 
            autoResize: true, 
            containerCss:{ borderColor:"#ccc", width:(wiki_type == "scraper" ? 480 : 630)+"px", height:"170px" }, 
            overlayCss: { cursor:"auto" }
        });
    });
}

$(function()
{ 
	setupSearchBoxHint();
	setupNavSearchBoxHint();

    $('a.editor_view').click(function()  {  newCodeObject('view');  return false; }); 
    $('a.editor_scraper').click(function()  {  newCodeObject('scraper');  return false; }); 
	
	function developer_show(){
		$('#intro_developer, #intro_requester, #blob_requester').fadeOut(500);
		$('#more_developer_div').fadeIn(500);
		$('#blob_developer').animate({left: 760}, 1000, 'easeOutCubic').addClass('active');
	}
	
	function developer_hide(){
		$('#intro_developer, #intro_requester, #blob_requester').fadeIn(500);
		$('#more_developer_div').fadeOut(500);
		$('#blob_developer').animate({left: 310}, 1000, 'easeOutCubic').removeClass('active');
	}
	
	function requester_show(){
		$('#intro_developer, #intro_requester, #blob_developer').fadeOut(500);
		$('#more_requester_div').fadeIn(500);
		$('#blob_requester').animate({left: 10}, 1000, 'easeOutCubic').addClass('active');
	}
	
	function requester_hide(){
		$('#intro_developer, #intro_requester, #blob_developer').fadeIn(500);
		$('#more_requester_div').fadeOut(500);
		$('#blob_requester').animate({left: 460}, 1000, 'easeOutCubic').removeClass('active');
	}
	
	$('#blob_developer').css('cursor', 'pointer').bind('click', function(){
	    if($(this).is('.active')){
	        developer_hide();
	    } else {
	        developer_show();
	    }
	    return false;
	});
	
	$('#blob_requester').css('cursor', 'pointer').bind('click', function(){
	    if($(this).is('.active')){
	        requester_hide();
	    } else {
	        requester_show();
	    }
	    return false;
	});
	
	$('#more_developer, #intro_developer').css('cursor', 'pointer').bind('click', function(){
		developer_show();
		return false;
	});

	$('#more_requester, #intro_requester').css('cursor', 'pointer').bind('click', function(){
		requester_show();
		return false;
	});

	
	$('#more_developer_div .back').live('click', function(){
		developer_hide();
		return false;
	});	
	$('#more_requester_div .back').live('click', function(){
		requester_hide();
		return false;
	});	
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

function setupDataViewer(){
    $('.raw_data').flexigrid({height:250});    
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
                    $('div.metadata dl').append('<dt>CKAN:</dt><dd><a href="http://ckan.net/package/'+ckan.package_id+'" target="_blank">link</a><dd>');
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


// all used only by the code_overview page
function setupScraperEditInPlace(wiki_type, short_name)
{
    //about
    $('#divAboutScraper').editable('admin/', {
             indicator : 'Saving...',
             tooltip   : 'Click to edit...',
             cancel    : 'Cancel',
             submit    : 'Save',
             type      : 'textarea',
             loadurl: 'raw_about_markup/',
             onblur: 'ignore',
             event: 'dblclick',
             submitdata : {short_name: short_name},
             placeholder: ''       
         });

    $('#aEditAboutScraper').click(
        function(){
             $('#divAboutScraper').dblclick();
             oHint = $('<div id="divMarkupHint" class="content_footer"><p><strong>You can use Textile markup to style the description:</strong></p><ul><li>*bold* / _italic_ / @code@</li><li>* Bulleted list item / # Numbered list item</li><li>"A link":http://www.data.gov.uk</li><li>h1. Big header / h2. Normal header</li></ul></div>');
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
         
    $('#aEditTitle').click(
        function(){
             $('#hCodeTitle').dblclick();
             return false;
        }
    );

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
    $('#aEditTags, #aEditTagsFromEmpty').click(function()
    {
        $('#divEditTags').dblclick();
        $('#divEditTagsControls').show();
        return false;
    });
    $('#divEditTagsControls').hide();
    $('#addtagmessage').css("display", ($("#divScraperTags ul.tags li a").length == 0 ? "block" : "none")); 


    // changing privacy status
    $('#spnPrivacyStatusChoice').editable($("#adminprivacystatusurl").val(), 
    {
        indicator : 'Saving...', tooltip:'Click to edit...', cancel:'Cancel', submit:'Save',
        onblur: 'ignore', event:'dblclick', placeholder:'', type: 'select', 
        data: optiontojson('#optionsPrivacyStatusChoices', $('#spnPrivacyStatusChoice').text()), 
        callback: function() { document.location.reload(true); }
    }); 
    $('#aPrivacyStatusChoice').click(function()  {  $('#spnPrivacyStatusChoice').dblclick(); });

    // changing editor status
    $('#addneweditor a').click(function()
    {
        $('#addneweditor a').hide()
        $('#addneweditor span').show(); 
    }); 
    $('#addneweditor input.cancelbutton').click(function()
    {
        $('#addneweditor span').hide(); 
        $('#addneweditor a').show()
    }); 
    $('#addneweditor input.addbutton').click(function()
    {
        var thisli = $(this).parents("li:first"); 
        var sdata = { roleuser:$('#addneweditor input:text').val(), newrole:'editor' }; 
        $.ajax({url:$("#admincontroleditors").val(), type: 'GET', data:sdata, success:function(result)
        {
            $('#addneweditor input:text').val(''); 
            if (result.substring(0, 6) == "Failed")
                alert(result); 
            else 
                document.location.reload(true)
        }}); 
        $('#addneweditor span').hide(); 
        $('#addneweditor a').show(); 
    }); 

    $('.demotebutton').click(function() 
    {
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'follow' }; 
        $.ajax({url:$("#admincontroleditors").val(), type: 'GET', data:sdata, success:function(result)
        {
            if (result.substring(0, 6) == "Failed")
                alert(result); 
            else 
                document.location.reload(true)
        }}); 
    }); 
    $('.promotebutton').click(function() 
    {
        var sdata = { roleuser:$(this).parents("li:first").find("span").text(), newrole:'editor' }; 
        $.ajax({url:$("#admincontroleditors").val(), type: 'GET', data:sdata, success:function(result)
        {
            if (result.substring(0, 6) == "Failed")
                alert(result); 
            else 
                document.location.reload(true)
        }}); 
    }); 



     //scheduler
     //
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

     //license
     $('#spnLicenseChoice').editable('admin/', {
              indicator : 'Saving...',
              tooltip   : 'Click to edit...',
              cancel    : 'Cancel',
              submit    : 'Save',
              onblur: 'ignore',
              data   : $('#hidLicenseChoices').val(),
              type   : 'select',
              event: 'dblclick',
              placeholder: '',
              submitdata : {short_name: short_name}
          });

      $('#aEditLicense').click (
           function(){
                sCurrent = $('#spnLicenseChoice').html().trim();
                $('#spnLicenseChoice').dblclick();
                $('#spnLicenseChoice select').val(sCurrent);
                return false;
           }
       );          
      

       $('#publishScraperButton').click(function(){
           $.ajax({
               url: 'admin/',
               data: {'id': 'publishScraperButton'},
               type: 'POST',
               success: function(){
                   $('#publishScraper').fadeOut();
               },
               error: function(){
                   alert("Something went wrong publishing this scraper. Please try again. If the problem continues please send a message via the feedback form.");
               }
           });
           return false;
       });
}
