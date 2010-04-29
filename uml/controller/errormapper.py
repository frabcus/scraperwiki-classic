import  sys
import  re

etmap = \
    {
    "ImportError"                       : "Import failed",
    "ZeroDivisionError"                 : "Division by zero",
    "IndexError"                        : "List index error",
    "NameError"                         : "Variable name error",
    "TypeError"                         : "Value type error",
    "AssertionError"                    : "Assertion failed",
    "CPUTimeExceeded"                   : "CPU time limit exceeded"
    }

eimap = \
    {
    "not all arguments converted during string formatting"  : "Formatting error"
    }

def mapExceptionType (etype, einfo) :

    try :
        return "%s: %s" % (etmap[etype], einfo)
    except :
        pass

    try :
        return "%s: %s" % (eimap[einfo], einfo)
    except :
        pass

    if etype == "KeyError"   :
        return "Dictionary key error: key '%s' not found" % einfo

    return "%s: %s" % (etype, einfo)

def mapException (e) :

    try :
        if e.__class__.__name__ == 'HTTPError' :
            return "HTTPError: %s" % e.msg
    except :
        pass

    etext = repr(sys.exc_info()[1])
    m = re.search (r"(.*)\('(.*)',\)", etext)
    if m :
        return mapExceptionType(m.group(1), m.group(2))
    m = re.search (r"(.*)\(\"(.*)\",\)", etext)
    if m :
        return mapExceptionType(m.group(1), m.group(2))
    m = re.search (r"(.*)\((.*),\)", etext)
    if m :
        return mapExceptionType(m.group(1), m.group(2))
    m = re.search (r"(.*)\(\)", etext)
    if m :
        return mapExceptionType(m.group(1), "")
    return etext


if __name__ == "__main__" :

    try :
        import bozo
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        1/0
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        1%0
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        1.0/0.0
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        "a" % 1
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        [0,1,2][3]
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        v=1
        v[0]
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        {0:0,1:1,2:2}[3]
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)

    try :
        badvar
    except Exception, e :
        print mapException (`sys.exc_info()[1]`)
