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

    var oPopup = $('<div id="popup"></div>');
    oPopup.modal();
    $('#popup').load('/' + wiki_type + 's/new/choose_template/?ajax=1&scraper_short_name=' + scraper_short_name')