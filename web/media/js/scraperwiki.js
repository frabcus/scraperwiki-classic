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

