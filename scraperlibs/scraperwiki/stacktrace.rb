
def getExceptionTraceback(e, code)
    lbacktrace = e.backtrace.reverse
    lbacktrace.pop

    exceptiondescription = e.to_s
    (filename, linenumber) = exceptiondescription.split(":")
    if (filename == "(eval)")
        lbacktrace.push(exceptiondescription)
    end

    stackdump = []
    for l in lbacktrace
        (filename, linenumber, funcname) = l.split(":")
        if filename == "(eval)"
           filename = "<string>"
        end

        nlinenumber = linenumber.to_i
        stackentry = {"file" => filename, "linenumber" => nlinenumber, "duplicates" => 1}
        #stackentry["furtherlinetext"] = l
        codelines = code.split("\n")
        if (nlinenumber >= 1) && (nlinenumber <= codelines.size)
            stackentry["linetext"] = codelines[nlinenumber-1]
        end
        stackdump.push(stackentry)
    end

    return { 'message_type' => 'exception', 'exceptiondescription' => exceptiondescription, "stackdump" => stackdump }
end

