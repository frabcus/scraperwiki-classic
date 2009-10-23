
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
           readOnly: false,
           tabMode: "spaces", 
           autoMatchParens: true,
           width: '100%',
           parserConfig: {'pythonVersion': 2, 'strictErrors': true}, 

       });
       
       $('#editor #clear').click(function() {
         $('#console').replaceWith('<iframe name="console" id="console" style="width:100%"></iframe>')
       })
       
       // $("#editor #run_script").click(function() {  
       //   // alert('asd')
       //    $('#editor').attr({
       //      target: "console",
       //      action: "http://localhost:9004/",
       //      });
       //    // $('#editor').attr("action", "console")
       //    // var foo = $('#editor').attr('action')
       //    // alert(foo)
       //    // $('#console').html('')
       //    // return false;
       // });  
       
    });
