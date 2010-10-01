import sys
import inspect
import traceback
import re
import urllib

def getExceptionTraceback(code):
    """Traceback that makes raw data available to javascript to process"""
    exc_type, exc_value, exc_traceback = sys.exc_info()   # last exception that was thrown
    codelines = code.splitlines()
    stackdump = [ ]
        # outer level is the controller, 
        # second level is the module call.
        # anything beyond is within a function.  
            # Move the function call description up one level to the correct place
    
    for frame, file, linenumber, func, lines, index in inspect.getinnerframes(exc_traceback, context=1)[1:]:  # skip outer frame
        stackentry = {"linenumber":linenumber, "file":file}
        if func != "<module>":
            args, varargs, varkw, locals = inspect.getargvalues(frame)
            funcargs = inspect.formatargvalues(args, varargs, varkw, locals, formatvalue=lambda value: '=%s' % repr(value))
            stackentry["furtherlinetext"] = "%s(%s)" % (func, funcargs)  # double brackets to make it stand out
        
        if file == "<string>" and 0 <= linenumber - 1 < len(codelines):
            stackentry["linetext"] = codelines[linenumber - 1]  # have to do this as context=1 doesn't work (it doesn't give me anything in lines)
        
        if stackdump and stackdump[-1] == stackentry:
            duplicates += 1
        else:
            if stackdump:
                stackdump[-1]["duplicates"] = duplicates
            stackdump.append(stackentry)
            duplicates = 0
        
        if file[:15] == "/usr/lib/python":
            break
        pass # assert file == "<string>"
        
    if stackdump:
        stackdump[-1]["duplicates"] = duplicates
    
    if exc_type in [ SyntaxError, IndentationError ]:
        stackentry = {"linenumber":exc_value.lineno, "file":exc_value.filename, "offset":exc_value.offset, "duplicates":1}
        if stackentry["file"] == "<string>" and 0 <= stackentry["linenumber"] - 1 < len(codelines):
            stackentry["linetext"] = codelines[stackentry["linenumber"] - 1]  # can't seem to recover the text from the SyntaxError object, though it is in it's repr
        stackentry["furtherlinetext"] = exc_value.msg
        stackdump.append(stackentry)
        
    # truncate the list
    if len(stackdump) > 50:
        stackdump = stackdump[:20] + [{"furtherlinetext": "%d entries omitted" % (len(stackdump)-40) }] + stackdump[-20:]
    
    result = { "exceptiondescription":repr(exc_value), "stackdump":stackdump }
    
    #raise IOError('http error', 403, 'Scraperwiki blocked access to "http://tits.ru/".  Click <a href="/whitelist/?url=http%3A//tits.ru/">here</a> for details.', <httplib.HTTPMessage instance at 0x84c318c>)
    if exc_type == IOError and len(exc_value.args) >= 2 and exc_value.args[1] == 403:
        mblockaccess = re.match('Scraperwiki blocked access to "(.*?)"', str(exc_value.args[2]))
        if mblockaccess:
            result["blockedurl"] = mblockaccess.group(1)
            result["blockedurlquoted"] = urllib.quote(mblockaccess.group(1))
    
    return result


