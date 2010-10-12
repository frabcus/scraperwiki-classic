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

    $('#popup').load('/' + wiki_type + 's/new/choose_template/?ajax=1',
        function() {
            $('#popup .popupClose').click(function(){
                $('#overlay').remove();
                $('#popup').remove();        
                return false;
            });
        }
    );

}
