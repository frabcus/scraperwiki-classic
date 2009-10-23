
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
       
       //setup dragging
       $("#resizebar").bind("mousedown", startDrag);   // see below
       
       
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

    // dragging of middle bar code -- could move into own javascript library
	var staticOffset;  
	var iLastMousePos = 0;
    var draggedWindow; 
    function mouseY(e) 
    { 
        return e.clientY + document.documentElement.scrollTop; 
    };

    function startDrag(e){
        iLastMousePos = mouseY(e);
        draggedWindow = $("#id_code").next().children(":first"); // this gets you to the iframe that you need to be resizing!!
        staticOffset = draggedWindow.height() - iLastMousePos;
        $(document).mousemove(performDrag).mouseup(endDrag);
    }
    function performDrag(e) 
    {        
        var iThisMousePos = mouseY(e);
        var iMousePos = staticOffset + iThisMousePos;
        if (iLastMousePos >= (iThisMousePos)) 
            iMousePos -= 5;
        iLastMousePos = iThisMousePos;
        //$("#Dout").text("mouse drag: " + iThisMousePos)
        iMousePos = Math.max(60, iMousePos);
        draggedWindow.height(iMousePos + 'px');
        return false;
        
        //TODO: scrollbars should never appear on this page - the output section
        //should be squished, and dragging stopped when only the buttons are visible
    }
    function endDrag(e) 
    {
        $(document).unbind('mousemove', performDrag).unbind('mouseup', endDrag);
        staticOffset = null;
        iLastMousePos = 0;
        draggedWindow = null; 
    }