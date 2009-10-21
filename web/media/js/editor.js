
$(document).ready(function()
{

    codeeditor = CodeMirror.fromTextArea("id_code", 
    {        
      parserfile: ["../contrib/python/js/parsepython.js"],
      stylesheet: "/media/CodeMirror-0.63/contrib/python/css/pythoncolors.css",
      path: "/media/CodeMirror-0.63/js/",
      textWrapping: false, 
      lineNumbers: true, 
      indentUnit: 4, 
      tabMode: "spaces", 
      autoMatchParens: true,
      parserConfig: {'pythonVersion': 2, 'strictErrors': true}, 

      // copies the value from the editor to the text area before submit.  
      // triggering the submit button causes the page to reload as it bypasses the whole ajax thing
      saveFunction: function () { $("#id_code").val(codeeditor.getCode());  $("#codewikiform").submit();  }
    });
});

