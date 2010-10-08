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
    var oPopup = $('<div id="popup" class="popup_item">');
    var oOverlay = $('<div id="overlay"></div></div>');

    oOverlay.show();
    $('body').append(oOverlay);
    $('body').append(oPopup);        

    // scraper_short_name is set in templates/codewiki/scraper_overview.html
    $('#popup').load('/' + wiki_type + 's/new/choose_template/?scraper_short_name=' + scraper_short_name,
        function() {
            $('#popup .popupClose').click(function(){
                $('#overlay').remove();
                $('#popup').remove();        
                return false;
            });
        }
    );
}
