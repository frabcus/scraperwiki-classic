function setupCodeViewer(iLineCount, scraperlanguage) {
    var oCodeEditor;
    if(iLineCount < 20)
        iLineCount = 20;

    var selrangefunc = function() {
        if (!((selrange[2] == 0) && (selrange[3] == 0))){
            linehandlestart = oCodeEditor.nthLine(selrange[0] + 1); 
            linehandleend = oCodeEditor.nthLine(selrange[2] + 1); 
            oCodeEditor.selectLines(linehandlestart, selrange[1], linehandleend, selrange[3]); 
        }; 
    }; 

    $(document).ready(function(){
        var parsers = Array();
        parsers['python'] = '../contrib/python/js/parsepython.js';
        parsers['php'] = ['../contrib/php/js/tokenizephp.js', '../contrib/php/js/parsephp.js'];
        parsers['ruby'] = ['../../ruby-in-codemirror/js/tokenizeruby.js', '../../ruby-in-codemirror/js/parseruby.js'];
        parsers['html'] = ['parsexml.js', 'parsecss.js', 'tokenizejavascript.js', 'parsejavascript.js', 'parsehtmlmixed.js']; 

        var stylesheets = Array();
        stylesheets['python'] = ['/media/CodeMirror/contrib/python/css/pythoncolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['php'] = ['/media/CodeMirror/contrib/php/css/phpcolors.css', '/media/css/codemirrorcolours.css']; 
        stylesheets['ruby'] = ['/media/ruby-in-codemirror/css/rubycolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['html'] = ['/media/CodeMirror/css/xmlcolors.css', '/media/CodeMirror/css/jscolors.css', '/media/CodeMirror/css/csscolors.css', '/media/css/codemirrorcolours.css']; 

        oCodeEditor = CodeMirror.fromTextArea("txtScraperCode", {
            parserfile: parsers[scraperlanguage],
            stylesheet: stylesheets[scraperlanguage],

            path: "/media/CodeMirror/js/",
            textWrapping: true, 
            lineNumbers: true, 
            indentUnit: 4,
            readOnly: true,
            tabMode: "spaces", 
            autoMatchParens: true,
            width: '100%',
            height: iLineCount + 'em', 
            parserConfig: {'pythonVersion': 2, 'strictErrors': true}, 

            // this is called once the codemirror window has finished initializing itself, (though happens to early, so that the selection gets deselected.  should file a bug)
            initCallback: function() { setTimeout(selrangefunc, 1000); }
        });
    });
}

function APISetupExploreFunction(){

    //link up the call button to change a few bits of text
    $('#btnCallMethod').click(
        function(){
            $('.explorer_response h2').html('Function response');
            return true;
        }
    );

    //change the sidebar examples to links where useful
    $('#ulFormats li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a href="#">' + sText + '</a>');
            aLink.click(
                function (){
                    $('#format').val(sText);
                    $('#format').focus();
                    rewriteApiUrl();                    
                }
            );
            $(this).html(aLink);
        }
    );

    $('#ulScraperShortNames li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a href="#">' + sText + '</a>');
            aLink.click(
                function (){
                    $('#name').val(sText);
                    $('#name').focus();
                    rewriteApiUrl();
                    return false;
                }
            );
            $(this).html(aLink);
        }
    );

    $('#ulApiKeys li code').each(
        function(){
            var sText = $(this).html();
            var aLink = $('<a href="#">' + sText + '</a>');
            aLink.click(
                function (){
                    $('#key').val(sText);
                    $('#key').focus();
                    rewriteApiUrl();
                    return false;
                }
            );
            $(this).html(aLink);
        }
    );

    //linkup the texboxes to rewrite the API url
    $('.api_arguments dl input').each(
        $(this).keyup(
            function(){
                rewriteApiUrl();
            }
        )
    );
}

function rewriteApiUrl (){
    sArgs = '?';
    var aControls = $('.api_arguments dl input')
    for (var i=0; i < aControls.length; i++) {
        if($(aControls[i]).val() != ''){
	        if (i > 0) {
            	sArgs += ('&');
        	}
            sArgs += (aControls[i].id + '=' + $(aControls[i]).val());
        }
    };
    $('#aApiLink span').html(sArgs);
    $('#aApiLink').attr('href', $('#uri').val() + sArgs);
}

function setupButtonConfirmation(sId, sMessage){
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

function setupHints(){
    $('#q').tbHinter({
    	text: 'Search ScraperWiki',
    	class: 'hint'
    });
}

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

function setupScraperEditInPlace(wiki_type, short_name){
    
    //about
    $('#divAboutScraper').editable('admin/', {
             indicator : 'Saving...',
             tooltip   : 'Click to edit...',
             cancel    : 'Cancel',
             submit    : 'Save',
             type      : 'textarea',
             loadurl: 'raw_about_markup/',
             event: 'dblclick',
             submitdata : {js: 1, short_name: short_name},
             placeholder: '',             
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
             indicator : 'Saving...',
             tooltip   : 'Click to edit...',
             cancel    : 'Cancel',
             submit    : 'Save',
             event: 'dblclick',
             placeholder: '',             
             submitdata : {js: 1, short_name: short_name},
         });
         
    $('#aEditTitle').click(
        function(){
             $('#hCodeTitle').dblclick();
             return false;
        }
    );

    //tags
    oDummy = $('<div id="divEditTags"></div>');
    $('#divScraperTags').append(oDummy);
    $('#divEditTags').editable('admin/', {
             indicator : 'Saving...',
             tooltip   : 'Click to edit...',
             cancel    : 'Cancel',
             submit    : 'Add tags',
             event: 'dblclick',
             placeholder: '',
             submitdata : {js: 1, short_name: short_name},
             callback: function (data){
                 //add the new tags onto the list
                 aItems = data.split(',');
                 $('#divScraperTags ul').html('');
                 for (var i=0; i < aItems.length; i++) {
                    url = '/' + wiki_type + 's/tags/' + escape(aItems[i].trim())
                    $('#divScraperTags ul').append($('<li><a href="' + url +'">' + aItems[i].trim() + '</a></li>'))
                 };
                 //clear out the textbox for next time
                 $('#divEditTags').html('');
            },
         });
    $('#aAddTags').click (
         function(){
              $('#divEditTags').dblclick();
              return false;
         }
     );

     //scheduler
     //alert(schedule_options.length)
     $('#spnRunInterval').editable('admin/', {
              indicator : 'Saving...',
              tooltip   : 'Click to edit...',
              cancel    : 'Cancel',
              submit    : 'Save',
              data   : $('#hidScheduleOptions').val(),
              type   : 'select',
              event: 'dblclick',
              placeholder: '',
              submitdata : {js: 1, short_name: short_name},
          });
      
      $('#aEditSchedule').click (
           function(){
                sCurrent = $('#spnRunInterval').html().trim();               
                $('#spnRunInterval').dblclick();
                $('#spnRunInterval select').val(sCurrent);
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
