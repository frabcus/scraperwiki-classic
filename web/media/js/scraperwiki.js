function setupCodeViewer(iLineCount){
    var oCodeEditor;
    if(iLineCount < 20){
        iLineCount = 20;
    }
    $(document).ready(function(){

       oCodeEditor = CodeMirror.fromTextArea("txtScraperCode", {
           parserfile: ["../contrib/python/js/parsepython.js"],
           stylesheet: "/media/CodeMirror-0.63/contrib/python/css/pythoncolors.css",

           path: "/media/CodeMirror-0.63/js/",
           textWrapping: false, 
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
                }
            );
            $(this).html(aLink);
        }
    );

}
