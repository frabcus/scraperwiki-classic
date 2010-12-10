
function highlightCode()
{
    var lineNo = 1; 
    var output = $('div#codepreviewer pre#output')[0]; //document.getElementById("output");
    var numbers = $('div#codepreviewer div#linenumbers')[0]; //document.getElementById("numbers");
 
    function addLine(line) 
    {
        numbers.appendChild(document.createTextNode(String(lineNo++)));
        numbers.appendChild(document.createElement("BR"));
        for (var i = 0; i < line.length; i++) 
            output.appendChild(line[i]);
        output.appendChild(document.createElement("BR"));
    }
    highlightText($('#inputcode_main').text(), addLine, Parser); 
}



function setupCodeViewer(iLineCount, scraperlanguage, codemirror_url) {
    var oCodeEditor;
    if(iLineCount < 20)
        iLineCount = 20;

    var selrangefunc = function() {
        if (!((selrange[2] == 0) && (selrange[3] == 0))){
            linehandlestart = oCodeEditor.nthLine(selrange[0] + 1); 
            linehandleend = oCodeEditor.nthLine(selrange[2] + 1); 
            oCodeEditor.selectLines(linehandlestart, selrange[1], linehandleend, selrange[3]); 
        }; 
    }; 

    $(document).ready(function(){

        var parsers = Array();
        parsers['python'] = '../contrib/python/js/parsepython.js';
        parsers['php'] = ['../contrib/php/js/tokenizephp.js', '../contrib/php/js/parsephp.js'];
        parsers['ruby'] = ['../../ruby-in-codemirror/js/tokenizeruby.js', '../../ruby-in-codemirror/js/parseruby.js'];
        parsers['html'] = ['parsexml.js', 'parsecss.js', 'tokenizejavascript.js', 'parsejavascript.js', 'parsehtmlmixed.js']; 

        var stylesheets = Array();
        stylesheets['python'] = [codemirror_url+'contrib/python/css/pythoncolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['php'] = [codemirror_url+'contrib/php/css/phpcolors.css', '/media/css/codemirrorcolours.css']; 
        stylesheets['ruby'] = ['/media/ruby-in-codemirror/css/rubycolors.css', '/media/css/codemirrorcolours.css'];
        stylesheets['html'] = [codemirror_url+'css/xmlcolors.css', codemirror_url+'css/jscolors.css', codemirror_url+'css/csscolors.css', '/media/css/codemirrorcolours.css']; 

        oCodeEditor = CodeMirror.fromTextArea("txtScraperCode", {
            parserfile: parsers[scraperlanguage],
            stylesheet: stylesheets[scraperlanguage],

            path: codemirror_url + "js/",
            textWrapping: true, 
            lineNumbers: true, 
            indentUnit: 4,
            readOnly: true,
            tabMode: "spaces", 
            autoMatchParens: true,
            width: '100%',
            height: iLineCount + 'em', 
            parserConfig: {'pythonVersion': 2, 'strictErrors': true}, 

            // this is called once the codemirror window has finished initializing itself, (though happens to early, so that the selection gets deselected.  should file a bug)
            initCallback: function() { setTimeout(selrangefunc, 1000); }
        });
    });
}

