
def getExceptionTraceback(e, code, code_filename)
    lbacktrace = e.backtrace.reverse
    #File.open("/tmp/fairuby", 'a') {|f| f.write(JSON.generate(lbacktrace)) }
    lbacktrace.pop

    exceptiondescription = e.to_s
    (filename, linenumber, message) = exceptiondescription.split(/[:\n]/) # there is more after 3rd, thrown away
    if (filename == "(eval)")
        if (message.strip == "compile error")
            # Special case for compile errors, where there are *two* errors in the exception description.
            # So in the case where we have more lines than the first one, and first is a compile error,
            # we can ditch the compile error - there is e.g. a syntax error in the rest of the description.
            lines = exceptiondescription.split("\n")
            if lines.size > 1
                # Remove the first line, with the compile error in it
                exceptiondescription = lines[1,lines.size()].join("\n")
            end
        end 

        lbacktrace.push(exceptiondescription)
    end

    stackdump = []
    for l in lbacktrace
        (filename, linenumber, funcname) = l.split(":")

        nlinenumber = linenumber.to_i
        stackentry = {"file" => filename, "linenumber" => nlinenumber, "duplicates" => 1}

        if filename == "(eval)"
            codelines = code.split("\n")
            if (nlinenumber >= 1) && (nlinenumber <= codelines.size)
                stackentry["linetext"] = codelines[nlinenumber-1]
            elsif (nlinenumber == codelines.size + 1)
                stackentry["linetext"] = "<end of file>"
            else
                stackentry["linetext"] = "getExceptionTraceback: ScraperWiki internal error, line %d out of range in file %s" % [nlinenumber, code_filename]
            end
            stackentry["file"] = "<string>"
        else
            # XXX bit of a hack to show the line number in third party libraries
            stackentry["file"] += ":" + linenumber
        end
        if funcname
            stackentry["furtherlinetext"] = funcname
        end
        stackdump.push(stackentry)
    end

    return { 'message_type' => 'exception', 'exceptiondescription' => exceptiondescription, "stackdump" => stackdump }
end

