import ast

# should be using docutils.rst2html.py in this, but not installed

def MakeDescriptionFromCode(language, code):
    if language != "python":
        return ""

    mnode = ast.parse(code)
    mdocstring = ast.get_docstring(mnode)
    if not mdocstring:
        return ""

    res = [ ]
        # should be using docutils.rst2html.py in this, but not installed
    paras = [ para.replace("<", "&lt;")  for para in mdocstring.split("\n\n")]
    res.append("<p>%s</p>" % "</p>\n<p>".join(paras))
    res.append("")
    
    funcnodes = [ node  for node in mnode.body  if type(node) == ast.FunctionDef]
    if funcnodes:
        res.append("<dl>")
        for fnode in funcnodes:
            res.append("<dt><b>%s(%s)</b></dt>" % (fnode.name, ", ".join([arg.id  for arg in fnode.args.args])))
            fdocstring = ast.get_docstring(fnode)
            if fdocstring:
                res.append("<dd>%s</dd>" % fdocstring.replace("<", "&lt;"))
        res.append("</dl>")
    else:
        res.append("<p>&lt;no functions&gt;</p>")
    return "\n".join(res)

