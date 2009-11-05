function setupCodeViewer(){
    var oCodeEditor;
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
           parserConfig: {'pythonVersion': 2, 'strictErrors': true}

       });
      });
}

