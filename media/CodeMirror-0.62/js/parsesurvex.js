/* Simple parser for Survex files (based on the CSS example) */

// The tokenizer breaks up the text into convincing chunks (I think the white-space is parser automatically)
var SVXParser = Editor.Parser = (function() {
  var tokenizeSVX = (function() {
    function normal(source, setState) {
      var ch = source.next();

      if (ch == ";") {
        source.nextWhile(matcher(/[^\n]/));
        return "svx-comment";
      }
      else if (ch == "*") {
        source.nextWhile(matcher(/\w/));
        return "svx-command";
      }
      else if (ch == "\"" || ch == "'") {
        var escaped = false;
        while (!source.endOfLine()) {
          var nch = source.next();
          if (nch == ch && !escaped)
            break;
          escaped = !escaped && nch == "\\";
        }
        return "svx-string";
      }
      else if (/[\d\-+.]/.test(ch)) {
        source.nextWhile(matcher(/[\d.]/));
        return "svx-measure";
      }
      else {
        source.nextWhile(matcher(/\S/));
        return "svx-word";
      }
    }

    return function(source, startState) {
      return tokenizer(source, startState || normal);
    };
  })();

  // survex doesn't have indentation; but you get double linefeeds if you leave this out.
  function indentSVX() {
    return function(nextChars) {
      return 0;
    };
  }

  // Then this simple parser fixes up the obvious errors made by the tokenizer (which could only operate on characters)
  // A very fancy upgrade could make it capable of handling the *data commands which make it accept different orderings of 
  // the parameters -- though this may be a challenge because the whole file needs reparsing when that happens -- don't 
  // know how optimized the basic code is to be able to call for such to happen when a formatting command like this changes.
  function parseSVX(source, basecolumn) {
    basecolumn = basecolumn || 0;
    var tokens = tokenizeSVX(source);
    var inCommand = false;
    var ntokeninline = -1; 

    var iter = {
      next: function() {
        var token = tokens.next(), style = token.style, content = token.content;

        if (content == "\n") {
            ntokeninline = -1; 
            inCommand = false; 
            token.indentation = indentSVX();
        }
        else if (style != "whitespace")
            ntokeninline += 1; 

        if (style == "svx-command") {
            inCommand = (ntokeninline == 0); 
            if (!inCommand)
                token.style = "svx-word";
            else if (content == "*begin")
                token.style = "svx-begin"; 
            else if (content == "*end")
                token.style = "svx-end"; 
        }

        if (!inCommand && style == "svx-measure") {
            if (ntokeninline < 2)
                token.style = "svx-word"; 
        }
        if (!inCommand && style == "svx-word" && (ntokeninline == 4)) {
            if (content == "down" || content == "up")
                token.style = "svx-measure"; 
        }

        return token;
      },

      copy: function() {
        var _inCommand = inCommand, _tokenState = tokens.state, _ntokeninline = ntokeninline; 
        return function(source) {
          tokens = tokenizeSVX(source, _tokenState);
          inCommand = _inCommand;
          ntokeninline = _ntokeninline; 
          return iter;
        };
      }
    };
    return iter;
  }

  return {make: parseSVX};
})();
