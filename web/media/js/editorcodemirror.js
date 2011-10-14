// editor window dimensions
var codeeditor = null;
var codemirroriframe = null; // the actual iframe of codemirror that needs resizing (also signifies the frame has been built)
var codeeditorreadonly = false; 
var codemirroriframeheightdiff = 0; // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
var codemirroriframewidthdiff = 0;  // the difference in pixels between the iframe and the div that is resized; usually 0 (check)
var previouscodeeditorheight = 0; //$("#codeeditordiv").height() * 3/5;    // saved for the double-clicking on the drag bar
var draftpreviewwindow = null;

var texteditor; // plain or codemirror

var parsers = Array();
var stylesheets = Array();
var indentUnits = Array();
var parserConfig = Array();
var parserName = Array();
var codemirroroptions = undefined; 

   // called from editortabs.js
function SelectEditorLine(iLine)
{
    codeeditor.selectLines(codeeditor.nthLine(iLine), 0, codeeditor.nthLine(iLine + 1), 0); 
}


//setup code editor
function setupCodeEditor()
{
    // destroy any existing codemirror, so we can remake it with right readonly state
    if (codeeditor) 
    {
        codeeditor.toTextArea("id_code"); 
        codeeditor = null;
        codemirroriframe = null;  // this only gets set once again when we know the editor has been initialized
    }

    // set other things readonly or not
    $('#id_title').attr("readonly", (codeeditorreadonly ? "yes" : ""));

    // just a normal textarea
    if (texteditor == "plain")
    {
        $('#id_code').keypress(function() { ChangeInEditor("edit"); }); 
        setupKeygrabs();
        resizeControls('first');
        $('#id_code').attr("readonly", (codeeditorreadonly ? "yes" : ""));
        setCodeeditorBackgroundImage(codeeditorreadonly ? 'url(/media/images/staff.png)' : 'none');
        return;
    }

    // codemirror
    parsers['python'] = ['../contrib/python/js/parsepython.js'];
    parsers['php'] = ['../contrib/php/js/tokenizephp.js', '../contrib/php/js/parsephp.js', '../contrib/php/js/parsephphtmlmixed.js' ];
    parsers['ruby'] = ['../../ruby-in-codemirror/js/tokenizeruby.js', '../../ruby-in-codemirror/js/parseruby.js'];
    parsers['html'] = ['parsexml.js', 'parsecss.js', 'tokenizejavascript.js', 'parsejavascript.js', 'parsehtmlmixed.js']; 
    parsers['javascript'] = ['tokenizejavascript.js', 'parsejavascript.js']; 

    stylesheets['python'] = [codemirror_url+'contrib/python/css/pythoncolors.css', '/media/css/codemirrorcolours.css'];
    stylesheets['php'] = [codemirror_url+'contrib/php/css/phpcolors.css', '/media/css/codemirrorcolours.css'];
    stylesheets['ruby'] = ['/media/ruby-in-codemirror/css/rubycolors.css', '/media/css/codemirrorcolours.css'];
    stylesheets['html'] = [codemirror_url+'/css/xmlcolors.css', codemirror_url+'/css/jscolors.css', codemirror_url+'/css/csscolors.css', '/media/css/codemirrorcolours.css']; 
    stylesheets['javascript'] = [codemirror_url+'/css/jscolors.css', '/media/css/codemirrorcolours.css']; 

    indentUnits['python'] = 4;
    indentUnits['php'] = 4;
    indentUnits['ruby'] = 2;
    indentUnits['html'] = 4;
    indentUnits['javascript'] = 4;

    parserConfig['python'] = {'pythonVersion': 2, 'strictErrors': true}; 
    parserConfig['php'] = {'strictErrors': true}; 
    parserConfig['ruby'] = {'strictErrors': true}; 
    parserConfig['html'] = {'strictErrors': true}; 
    parserConfig['javascript'] = {'strictErrors': true}; 

    parserName['python'] = 'PythonParser';
    parserName['php'] = 'PHPHTMLMixedParser'; // 'PHPParser';
    parserName['ruby'] = 'RubyParser';
    parserName['html'] = 'HTMLMixedParser';
    parserName['javascript'] = 'JSParser';

    // allow php to access HTML style parser
    parsers['php'] = parsers['html'].concat(parsers['php']);
    stylesheets['php'] = stylesheets['html'].concat(stylesheets['php']); 

    // track what readonly state we thought we were going to, in case it
    // changes mid setup of CodeMirror
    var expectedreadonly = codeeditorreadonly;

    codemirroroptions = {
        parserfile: parsers[scraperlanguage],
        stylesheet: stylesheets[scraperlanguage],
        path: codemirror_url + "js/",
        domain: document.domain, 
        textWrapping: true,
        lineNumbers: true,
        indentUnit: indentUnits[scraperlanguage],
        readOnly: expectedreadonly, // cannot be changed once started up
        undoDepth: 200,  // defaults to 50.  
        undoDelay: 300,  // (default is 800)
        tabMode: "shift", 
        disableSpellcheck: true,
        autoMatchParens: true,
        width: '100%',
        parserConfig: parserConfig[scraperlanguage],
        enterMode: "flat",    // default is "indent" (which I have found buggy),  also can be "keep"
        electricChars: false, // default is on, the auto indent whe { is typed (annoying when doing html)
        reindentOnLoad: false, 
        onChange: function ()  { ChangeInEditor("edit"); },  // (prob impossible to tell difference between actual typing and patch insertions from another window)
        //noScriptCaching: true, // essential when hacking the codemirror libraries

        // this is called once the codemirror window has finished initializing itself
        initCallback: function() 
        {
            codemirroriframe = codeeditor.frame // $("#id_code").next().children(":first"); (the object is now a HTMLIFrameElement so you have to set the height as an attribute rather than a function)
            codemirroriframeheightdiff = codemirroriframe.height - $("#codeeditordiv").height(); 
            codemirroriframewidthdiff = codemirroriframe.width - $("#codeeditordiv").width(); 
            setupKeygrabs();
            resizeControls('first');
            ChangeInEditor("initialized"); 

            // set up other readonly values, after rebuilding the CodeMirror editor
            setCodeeditorBackgroundImage(expectedreadonly ? 'url(/media/images/staff.png)' : 'none');

            if (expectedreadonly) {
                $('.editor_controls #btnCommitPopup').hide();
                $('.editor_controls #btnForkNow').show();
            } else {
                $('.editor_controls #btnCommitPopup').show();
                $('.editor_controls #btnForkNow').hide();
            }

            // our readonly state was changed under our feet while setting
            // up CodeMirror; force a resetup of CodeMirror again
            if (expectedreadonly != codeeditorreadonly) 
            {
                var lcodeeditorreadonly = codeeditorreadonly; 
                codeeditorreadonly = expectedreadonly;  // set it back 
                setCodeMirrorReadOnly(lcodeeditorreadonly);
            }
        } 
    };

    // now puts it in a state of building where codeeditor!=null and codemirroriframe==null
    codeeditor = CodeMirror.fromTextArea("id_code", codemirroroptions); 
}



function setCodeMirrorReadOnly(val) 
{
    if (codeeditorreadonly == val) 
        return;
    codeeditorreadonly = val;
    writeToChat('set codemirror editor to ' + (codeeditorreadonly ? "readonly" : "editable")); 

        // this rebuilds the entire code editor again!!!
    window.setTimeout(setupCodeEditor, 1); 
}

function setCodeeditorBackgroundImage(lcodeeditorbackgroundimage)
{
    if (codemirroriframe) // also signifies the frame has been built
        codeeditor.win.document.body.style.backgroundImage = lcodeeditorbackgroundimage; 
    else
        $('#id_code').css("background-image", lcodeeditorbackgroundimage); 
}


//resize code editor
function resizeCodeEditor()
{
    if (codemirroriframe)
    {
        //resize the iFrame inside the editor wrapping div
        codemirroriframe.height = (($("#codeeditordiv").height() + codemirroriframeheightdiff) + 'px');
        codemirroriframe.width = (($("#codeeditordiv").width() + codemirroriframewidthdiff) + 'px');

        //resize the output area so the console scrolls correclty
        iWindowHeight = $(window).height();
        iEditorHeight = $("#codeeditordiv").height();
        iControlsHeight = $('.editor_controls').height();
        iCodeEditorTop = parseInt($("#codeeditordiv").position().top);
        iOutputEditorTabs = $('#outputeditordiv .tabs').height();
        iOutputEditorDiv = iWindowHeight - (iEditorHeight + iControlsHeight + iCodeEditorTop) - 30; 
        $("#outputeditordiv").height(iOutputEditorDiv + 'px');   
        //$("#outputeditordiv .info").height($("#outputeditordiv").height() - parseInt($("#outputeditordiv .info").position().top) + 'px');
        $("#outputeditordiv .info").height((iOutputEditorDiv - iOutputEditorTabs) + 'px');
        //iOutputEditorTabs
    }
    else
    {
        $("#id_code").css("height", ($("#codeeditordiv").height()-10) + 'px'); 
        $("#id_code").css("width", ($("#codeeditordiv").width()-8) + 'px'); 
    }
}


//click bar to resize
function resizeControls(sDirection) 
{
    if (sDirection == 'first')
        previouscodeeditorheight = $(window).height() * 3/5; 
    else if (sDirection != 'up' && sDirection != 'down')
        sDirection = 'none';

    //work out which way to go
    var maxheight = $("#codeeditordiv").height() + $(window).height() - ($("#outputeditordiv").position().top + 5); 
    if (($("#codeeditordiv").height() + 5 <= maxheight) && (sDirection == 'none' || sDirection == 'down')) 
    {
        previouscodeeditorheight = $("#codeeditordiv").height();
        $("#codeeditordiv").animate({ height: maxheight }, 100, "swing", resizeCodeEditor); 
    } 
    else if ((sDirection == 'first') || (sDirection == 'none') || ((sDirection == 'up') && ($("#codeeditordiv").height() + 5 >= maxheight)))
        $("#codeeditordiv").animate({ height: Math.min(previouscodeeditorheight, maxheight - 5) }, 100, "swing", resizeCodeEditor); 
}

