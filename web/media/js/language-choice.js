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

function newCodeObject(wiki_type)
{
    url = '/' + wiki_type + 's/new/choose_template/?ajax=1';
    if (scraper_short_name != '')
        url += '&sourcescraper=' + scraper_short_name; 
    
    $.get(url, function(data) 
    {
        $.modal('<div id="template_popup">'+data+'</div>', 
        {
            overlayClose: true, 
            autoResize: true, 
            containerCss:{ borderColor:"#0ff", width:(wiki_type == "scraper" ? 500 : 750)+"px" }, 
            overlayCss: { cursor:"auto" }
        });
    });
}