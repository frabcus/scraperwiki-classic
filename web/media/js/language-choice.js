var scraper_short_name = '';  // reset in templates/codewiki/scraper_overview.html

$(function(){
    $('a.editor_view').click(function(){
        newCodeObject('view')
        return false;
    });

    $('a.editor_scraper').click(function(){
        newCodeObject('scraper')
        return false;
    });
});

function newCodeObject(wiki_type){

    var oPopup = $('<div id="template_popup"></div>');
    oPopup.modal();
    url = '/' + wiki_type + 's/new/choose_template/?ajax=1';
    if (scraper_short_name != ''){
        url += '&scraper_short_name=' + scraper_short_name
    }
    $('#template_popup').load(url, 
            function(){
                $('#simplemodal-container').css('height', 'auto');    
                $(window).resize();
        });

}