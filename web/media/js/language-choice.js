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
    $('#popup').load('/' + wiki_type + 's/new/choose_template/',
        function() {
            var oCloseLink = $('<a href="#">close</a>');            
            $('#popup').append(oCloseLink);            
            oCloseLink.click(function(){
                $('#overlay').remove();
                $('#popup').remove();        
                return false;
            });
        }
    );
}
