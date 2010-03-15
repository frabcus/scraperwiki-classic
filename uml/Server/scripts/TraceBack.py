#   Code in the module is taken from Ka-Ping Yee's cgitb.py module,
#   reformatted somewhat, and modified for ScraperWiki. Many thanks to
#   Ka-Ping Yee for this code.
#
import	os
import	types
import	time
import	traceback
import	linecache
import	inspect
import	pydoc
import	sys
import	string

__UNDEF__ = []                          # a special sentinel object

scraper	  = None

def strong (text) :

    """
    Format text within the "strong" tag

    @type	text	: String
    @param	text	: Text to format
    """

    if text :
        return '<strong>' + text + '</strong>'
    return ''

def small (text) :

    """
    Format text within the "small" tag

    @type	text	: String
    @param	text	: Text to format
    """

    if text :
        return '<small>' + text + '</small>'
    return ''


def grey (text) :

    """
    Format text as grey

    @type	text	: String
    @param	text	: Text to format
    """

    if text :
        return '<font color="#909090">' + text + '</font>'
    return ''


def lookup (name, frame, locals) :

    """
    Look up a variable in the specified frame and locals.

    @type	name	: String
    @param	name	: Variable to look up
    @type	frame	: Frame
    @param	frame	: Frame to search
    @type	locals	: Dictionary
    @param	locals	: Local varaiables
    """

    if name in locals :
        return 'local', locals[name]

    if name in frame.f_globals :
        return 'global', frame.f_globals[name]

    if '__builtins__' in frame.f_globals :
        builtins = frame.f_globals['__builtins__']
        if type(builtins) is type({}) :
            if name in builtins :
                return 'builtin', builtins[name]
        else :
            if hasattr(builtins, name) :
                return 'builtin', getattr(builtins, name)

    return None, __UNDEF__


def scanvars (reader, frame, locals) :

    import tokenize, keyword
    vars, lasttoken, parent, prefix, value = [], None, None, '', __UNDEF__

    for ttype, token, start, end, line in tokenize.generate_tokens(reader) :

        if ttype == tokenize.NEWLINE :
            break

        if ttype == tokenize.NAME and token not in keyword.kwlist :
            if lasttoken == '.' :
                if parent is not __UNDEF__ :
                    value = getattr (parent, token, __UNDEF__)
                    vars.append ((prefix + token, prefix, value))
            else:
                where, value = lookup (token, frame, locals)
                vars.append ((token, where, value))
        elif token == '.' :
            prefix += lasttoken + '.'
            parent  = value
        else :
            parent, prefix = None, ''

        lasttoken = token

    return vars


def checkScraper (file, lines, index, lnum, context) :

    if file == '<string>' :
        flno = lnum - context/2
        if flno < 0 : flno = 0
        return 'Scraper',  scraper[flno : flno + context], lnum - flno

    return os.path.abspath(file) or '?', lines, index


#  html
#  ----
#  Format traceback in HTML
#
def html ((etype, evalue, etb), context = 5) :

    if type(etype) is types.ClassType :
        etype = etype.__name__

    etext   = str(etype)
    pyver   = 'Python ' + sys.version.split()[0] + ': ' + sys.executable
    date    = time.ctime (time.time())
    head    = '<span class="scraper_traceback">' + \
			pydoc.html.heading \
			(
				'<big><big>%s</big></big>' % strong(pydoc.html.escape(etext)),
				'#ffffff',
				'#6622aa',
				pyver + '<br>' + date
			) + \
			'<p></p>'

    indent  = '<tt>' + small('&nbsp;' * 5) + '&nbsp;</tt>'
    infile  = None
    atline  = None
    frames  = []

    records = inspect.getinnerframes (etb, context)
    for frame, file, lnum, func, lines, index in records :

        file, lines, index = checkScraper (file, lines, index, lnum, context)

        link   = pydoc.html.escape(file)
        call   = ''

        args, varargs, varkw, locals = inspect.getargvalues(frame)

        if func != '?' :
            call = 'in ' + strong(func) + \
			inspect.formatargvalues \
			(	args,
				varargs,
				varkw,
				locals,
				formatvalue = lambda value: '=' + pydoc.html.repr(value)
			)

        hilite = {}

        def reader (lnum=[lnum]) :
            hilite[lnum[0]] = 1
            try     :
                if file == 'Scraper' :
                    return scraper[lnum[0]]
                return linecache.getline(file, lnum[0])
            finally :
                lnum[0] += 1

        vars   = scanvars(reader, frame, locals)

        rows   = [ '<tr><td bgcolor="#d8bbff"><big>&nbsp;</big>%s %s</td></tr>' % (link, call) ]

        if index is not None :
            i = lnum - index
            for line in lines :
                num  = small('&nbsp;' * (5-len(str(i))) + str(i)) + '&nbsp;'
                line = '<tt>%s%s</tt>' % (num, pydoc.html.preformat(line))
                if i in hilite :
                       rows.append ('<tr><td bgcolor="#ffccee">%s</td></tr>' % line)
                else : rows.append ('<tr><td>%s</td></tr>'                   % grey(line))
                i += 1

        done, dump = {}, []

        for name, where, value in vars :

            if name in done :
                continue

            done[name] = 1
            if value is not __UNDEF__ :
                if   where == 'global'  : name = '<em>global</em> '  + strong(name)
                elif where == 'builtin' : name = '<em>builtin</em> ' + strong(name)
                elif where == 'local'	: name = strong(name)
                else			: name = where + strong(name.split('.')[-1])
                dump.append('%s&nbsp;= %s' % (name, pydoc.html.repr(value)))
                continue

            dump.append(name + ' <em>undefined</em>')

        rows  .append ('<tr><td>%s</td></tr>' % small(grey(', '.join(dump))))
        frames.append \
		(	'''
			<table width="100%%" cellspacing=0 cellpadding=0 border=0>
			  %s
			</table>
			''' % '\n'.join(rows)
		)

        if infile is None :
            if file[:4] != '/usr' and file.find('/scripts/') < 0 :
                infile = file
                atline = lnum

        exception = \
		[	'<p>%s: %s' % (strong(pydoc.html.escape(etext)),
                         pydoc.html.escape(str(evalue)))
		]

    if type(evalue) is types.InstanceType :
        for name in dir(evalue) :
            if name[:1] == '_': continue
            value = pydoc.html.repr(getattr(evalue, name))
            exception.append('\n<br>%s%s&nbsp;=\n%s' % (indent, name, value))

    return etext, head + ''.join(frames) + ''.join(exception) + '<p>%{closer}</p>' + '</span>', infile, atline


#  text
#  ----
#  Format traceback as text
#
def text ((etype, evalue, etb), context=5) :

    if type(etype) is types.ClassType :
        etype = etype.__name__

    etext   = str(etype)
    pyver   = 'Python ' + sys.version.split()[0] + ': ' + sys.executable
    date    = time.ctime(time.time())
    head    = "%s\n%s\n%s\n" % (etext, pyver, date)
    infile  = None
    atline  = None
    frames  = []

    records = inspect.getinnerframes (etb, context)
    for frame, file, lnum, func, lines, index in records :

        file, lines, index = checkScraper (file, lines, index, lnum, context)

        call   = ''

        args, varargs, varkw, locals = inspect.getargvalues(frame)

        if func != '?' :
            call = 'in ' + func + \
			inspect.formatargvalues \
			(	args,
				varargs,
				varkw,
				locals,
				formatvalue = lambda value: '=' + pydoc.text.repr(value)
			)

        hilite = {}

        def reader (lnum=[lnum]) :
            hilite[lnum[0]] = 1
            try     :
                if file == 'Scraper' :
                    return scraper[lnum[0]]
                return linecache.getline(file, lnum[0])
            finally :
                lnum[0] += 1

        vars = scanvars(reader, frame, locals)

        rows = [ ' %s %s' % (file, call) ]

        if index is not None :

            i = lnum - index
            for line in lines:
                num = '%5d ' % i
                rows.append(num+line.rstrip())
                i += 1

        done, dump = {}, []

        for name, where, value in vars :

            if name in done :
                continue

            done[name] = 1
            if value is not __UNDEF__ :
                if   where == 'global'  : name = 'global '  + name
                elif where == 'builtin' : name = 'builtin ' + name
                elif where == 'local'   : pass
                else                    : name = where + name.split('.')[-1]
                dump.append('%s = %s' % (name, pydoc.text.repr(value)))
                continue

            dump.append(name + ' undefined')

        rows  .append ('\n'           .join(dump))
        frames.append ('\n%s\n' % '\n'.join(rows))

        if infile is None :
            if file[:4] != '/usr' and file.find('/scripts/') < 0 :
                infile = file
                atline = lnum

    exception = ['%s: %s' % (etext, str(evalue))]

    if type(evalue) is types.InstanceType :
        for name in dir(evalue) :
            if name[:1] == '_': continue
            value = pydoc.text.repr(getattr(evalue, name))
            exception.append('\n%s%s = %s' % (" "*4, name, value))

    return etext, head + ''.join(frames) + ''.join(exception) + '\n', infile, atline


#  traceback
#  ---------
#  Generate traceback in requested format.
#
def traceBack (format, code, info = None, context = 5) :

    global scraper
    scraper   = string.split ('\n' + code + '\n', '\n')
    info      = info or sys.exc_info()
    formatter = (format == "html") and html or text

    try    :
        res = formatter(info, context)
    except :
        tb  = ''.join(traceback.format_exception(*info))
        if format == "html" :
            tb  = res.replace('&', '&amp;').replace('<', '&lt;')
        res = '', tb, None, None

    return res
