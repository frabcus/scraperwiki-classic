
function highlightCode(code, Parser)
{
    var lineNo = 1; 
    var output = $('#codepreviewer #output'); 
    var numbers = $('#codepreviewer #linenumbers')
 
    function addLine(line) 
    {
        numbers.append(String(lineNo++)+'<br>'); 
        var kline = $('<span>').css('background-color', '#fae7e7'); 
        for (var i = 0; i < line.length; i++) 
            output.append(line[i]);
        output.append('<br>')
    }
    highlightText(code, addLine, Parser); 
}

function highlightOtherCode(code, othercode, matcheropcodes, Parser)
{
    var output = $('#codepreviewer #output'); 
    var numbers = $('#codepreviewer #linenumbers'); 
    var othernumbers = $('#codepreviewer #otherlinenumbers'); 

    // syntax highlight the two versions of the code
    var codelines = [ ]
    var othercodelines = [ ]
    highlightText(code, function(line) { codelines.push(line) }, Parser); 
    highlightText(othercode, function(line) { othercodelines.push(line) }, Parser); 

    var flinepadding = 2; 
    for (var k = 0; k < matcheropcodes.length; k++)
    {
        var mc = matcheropcodes[k];  // set from get_opcodes from http://docs.python.org/library/difflib.html
        var tag = mc[0]; i1 = mc[1]; i2 = mc[2]; j1 = mc[3]; j2 = mc[4]; 
        if (tag == "equal")
        {
            var li1 = (i1 == 0 ? 0 : i1 + flinepadding); 
            var li2 = (i2 == codelines.length ? i2 : i2 - flinepadding);
            for (var i = i1; i < i2; i++)
            {
                var eclass = ((i >= li1) && (i < li2) ? 'fequal' : 'equal'); 
                numbers.append('<span class="'+eclass+'">'+String(i+1)+'<br></span>'); 
                othernumbers.append('<span class="'+eclass+'">'+String(i-i1+j1+1)+'<br></span>'); 

                var fline = $('<span class="'+eclass+'">'); 
                var line = codelines[i]; 
                for (var m = 0; m < line.length; m++) 
                    fline.append(line[m]);
                fline.append('<br>'); 
                output.append(fline);
            }
        }

        else
        {
            for (var i = i1; i < i2; i++)
            {
                numbers.append('<span class="insert">'+String(i+1)+'<br></span>'); 
                othernumbers.append('<span class="insert">+<br></span>'); 

                var fline = $('<span class="insert">')
                var line = codelines[i]; 
                for (var m = 0; m < line.length; m++) 
                    fline.append(line[m]);
                fline.append('<br>'); 
                output.append(fline);
            }

            for (var j = j1; j < j2; j++)
            {
                numbers.append('<span class="delete">-<br></span>'); 
                othernumbers.append('<span class="delete">'+String(j+1)+'<br></span>'); 

                var fline = $('<span class="delete">')
                var line = othercodelines[j]; 
                for (var m = 0; m < line.length; m++) 
                    fline.append(line[m]);
                fline.append('<br>'); 
                output.append(fline);
            }
        }
    }
}

