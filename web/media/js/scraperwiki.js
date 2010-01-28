function setupCodeViewer(iLineCount){
    var oCodeEditor;
    if(iLineCount < 20){
        iLineCount = 20;
    }
    $(document).ready(function(){

       oCodeEditor = CodeMirror.fromTextArea("txtScraperCode", {
           parserfile: ["../contrib/python/js/parsepython.js"],
           stylesheet: "/media/CodeMirror-0.65/contrib/python/css/pythoncolors.css",

           path: "/media/CodeMirror-0.65/js/",
           textWrapping: true, 
           lineNumbers: true, 
           indentUnit: 4,
           readOnly: true,
           tabMode: "spaces", 
           autoMatchParens: true,
           width: '100%',
           height: iLineCount + 'em',           
           parserConfig: {'pythonVersion': 2, 'strictErrors': true}

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
    sArgs = '?key=[your api key]';
    var aControls = $('.api_arguments dl input')
    for (var i=0; i < aControls.length; i++) {
        if($(aControls[i]).val() != ''){
            sArgs += ('&' + aControls[i].id + '=' + $(aControls[i]).val());
        }
    };
    $('#aApiLink span').html(sArgs);
    $('#aApiLink').attr('href', $('#uri').val() + sArgs);
}
