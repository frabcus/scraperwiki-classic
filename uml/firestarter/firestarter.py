import  sys
import  resource
import  string
import  time
import  inspect
import  os
import  hashlib
import  ConfigParser
import  urllib2
import  cStringIO

try:
    import simplejson as json
except:
    import json

class FireWrapper :

    """
    Wrapper class to provide a "readline" method on the HTTP response
    object.
    """

    def __init__ (self, resp) :

        """
        Class constructor

        @type   resp    : Python HTTP response object
        @param  resp    : Python HTTP response object
        """

        ###
        ###  HACK ALERT:
        ###  Python 2.5 seems to think we should not allow small reads. Well,
        ###  bugger that, we know what we want.
        ###
        resp.fp._rbufsize = 1

        self.m_resp    = resp
        self.m_pending = cStringIO.StringIO()

    def read (self, n = None) :

        """
        Read data, possibly limited. May thrown an exception if one is
        passed back from the controller.

        Bug: If the read limit is set and the exception marker text is
        split, then the exception will be lost.

        @type   n   : Integer
        @param  n   : Read limit or None for unlimited
        """

        data    = self.m_resp.read (n)
        return data

    def readline (self) :

        """
        Read a line of data, up to the next '\n' character. Returns
        an empty at the end of the file. May thrown an exception if one is
        passed back from the controller.

        @rtype      : String
        @return     : Line of data or empty and end of file
        """

        ###
        ###  NOTE:
        ###  Need to change code to replace "self.m_resp.read (1)" with
        ###  sensible code that sets the stream to non-blocking mode and
        ###  uses "select".
        ###
        while True :
            more = self.m_resp.read (1)
            if more is None or more == '' :
                break
            self.m_pending.write(more)
            if more == '\n' :
                break
        res = self.m_pending.getvalue()
        self.m_pending.close()
        self.m_pending = cStringIO.StringIO()
        return res


class FireStarter :

    """
    This class provides an interface to the FireBox UML subsystem. The
    mechanism is to create an instance of this class, set the required
    options, and then execute it. The result from the execution call is
    the output from whatever is run under the controller in the UML
    box.
    """

    def __init__ (self, config) :

        """
        Class constructor.
        """

        self.m_conf        = ConfigParser.ConfigParser()
        self.m_conf.readfp (open(config))


        self.m_dispatcher  = None
        self.m_path        = ''
        self.m_parameters  = {}
        self.m_environment = {}
        self.m_user        = None
        self.m_group       = None
        self.m_limits      = {}
        self.m_allowed     = []
        self.m_blocked     = []
        self.m_paths       = []
        self.m_testName    = None
        self.m_runID       = None
        self.m_scraperID   = None
        self.m_urlquery   = None
        self.m_traceback   = None
        self.m_error       = None
        self.m_cache       = 0
        self.m_language    = None

        s = hashlib.sha1()
        s.update(str(os.urandom(16)))
        s.update(str(os.getpid (  )))
        s.update(str(time.time (  )))
        self.m_runID       = '%.6f_%s' % (time.time(), s.hexdigest())

        import swlogger
        self.m_swlog = swlogger.SWLogger(config)
        self.m_swlog.connect ()
        self.m_swlog.log     (self.m_scraperID, self.m_runID, 'F.START')

    def __del__ (self) :

        self.m_swlog.log     (self.m_scraperID, self.m_runID, 'F.END')

    def error (self) :

        """
        Return error string

        @rtype      : String
        @return     : Error string or None if no error
        """

        return self.m_error

    def setDispatcher (self, dispatcher) :

        """
        Set the dispatcher address as I{host:port}.

        @type   dispatcher  : String
        @param  dispatcher  : Dispatcher address as I{host:port}
        """

        self.m_dispatcher = dispatcher

    def setPath      (self, path) :

        """
        Set the URL path. This will be decoded by the UML controller to
        determin what sort of action to run. See the L{command} and
        L{execute} methods.

        @type   path    : String
        @param  path    : URL path, used by controller to determin action
        """

        self.m_path = path

    def setParameter (self, name, value) :

        """
        Set a parameter to be passed through (as a CGI encoded parameter)
        to the UML controller.

        @type   name    : String
        @param  name    : Parameter name
        @type   value   : String
        @param  value   : Parameter value
        """

        self.m_parameters[name] = value

    def setParameters (self, **params) :

        """
        Set multiple parameters passed as one or more keyed arguments.

        @type   params  : Dictionary
        @param  params  : Dictionary of name,value pairs
        """

        for name, value in params.items() :
            self.setParameter (name, value)

    def setEnvironment (self, name, value) :

        """
        Set an environment setting to be passed through
        to the UML controller.

        @type   name    : String
        @param  name    : Environment name
        @type   value   : String
        @param  value   : Environment value
        """

        self.m_environment[name] = value

    def setScraperID (self, scraperID) :

        """
        Set the scraper identifier

        @type   scraperID : String
        @param  scraperID : Scraper identifier
        """

        self.m_scraperID = scraperID

    def setUrlquery (self, urlquery) :

        """
        Set the urlquery string

        @type   urlquery : String
        @param  urlquery : Value
        """

        self.m_urlquery = urlquery
    
    def setUser (self, user) :

        """
        Set user that command or script will execute as

        @type   user    : String
        @param  user    : User name
        """

        self.m_user = user

    def setGroup (self, group) :

        """
        Set group that command or script will execute as

        @type   user    : String
        @param  user    : Group name
        """

        self.m_group = group

    def setLimit (self, resource, soft, hard = None) :

        """
        Set a process limit for the executed command or script. The
        resources to be controlled are defined in the I{resource}
        module, for instance I{resource.RLIMIT_CPU}

        @type   resource    : Integer
        @param  resource    : Resource to be controlled
        @type   soft        : Integer
        @param  soft        : Soft limit
        @type   hard        : Integer
        @param  hard        : Hard limit, defaults to soft limit
        """

        if hard is None : hard = soft
        self.m_limits[resource] = [ soft, hard ]

    def setLimits (self, **limits) :

        """
        Set multiple process resource limits. These should be passed
        as keyed arguments, in the form resource = [ soft, hard ] (or
        resource = [ soft ] to default the hard limit).

        @type   limits  : Dictionary
        @param  limits  : Dictionary of resource limits, keyed on resource
        """

        for resource, limit in limits :
            self.setLimit (resource, *limit)

    def setCache (self, cache) :

        """
        Set time for which cached pages are valid

        @type   cache   : Integer
        @param  cache   : Time for which pages are valid, zero means no caching
        """

        self.m_cache = cache

    def setLanguage (self, language) :

        """
        Set scripting language

        @type   language: String
        @param  language: Scripting language
        """

        self.m_language = language

    def addAllowedSites (self, *sites) :

        """
        Add sites which the scraper will be allowed to access. The
        sites terms are regular expressions whicn are anchor matched,
        for instance I{.*\.org\.uk} will allow all .org.uk sites.
        Multiple sites can be added as multiple arguments.

        @type   sites   : List
        @param  sites   : List of regular expressions matching sites
        """

        for site in sites :
            self.m_allowed.append (site)

    def addBlockedSites (self, *sites) :

        """
        Add sites which the scraper will block access to. The
        sites terms are regular expressions whicn are anchor matched,
        for instance I{.*\.org\.uk} will block all .org.uk sites.
        Multiple sites can be added as multiple arguments.

        @type   sites   : List
        @param  sites   : List of regular expressions matching sites
        """

        for site in sites :
            self.m_blocked.append (site)

    def loadConfiguration (self) :

        """
        Load configuration as retrieved from the configuration URL.
        """

        confurl = self.m_conf.get('dispatcher', 'confurl')
        if confurl != "allwhite":
            try:
                conftxt = urllib2.urlopen(confurl).read().replace('\r', '')
            except:
                if confurl[:26] == 'http://dev.scraperwiki.com':
                    pass  # known problem
                else:
                    print json.dumps({ 'message_type':'console', 'content': "Failed to open: %s" % confurl })
                conftxt = ""
        else:
            conftxt = "white=.*"  # hard code the whitelist to avoid accessing it (better for local versions)
            
        for line in conftxt.split('\n') :
            try :
                key, value = line.split('=')
                if key == 'white' :
                    self.addAllowedSites (value)
                    continue
                if key == 'black' :
                    self.addBlockedSites (value)
                    continue
            except :
                pass

        # Ticket 325
        #
        if self.m_conf.has_option ('dispatcher', 'path') :
            self.addPaths (*self.m_conf.get('dispatcher', 'path').split(','))

        self.setDispatcher  ('%s:%d' % (self.m_conf.get('dispatcher', 'host'), self.m_conf.getint('dispatcher', 'port')))

    def addPaths (self, *paths) :

        """
        Add directory paths to be added to the python search path
        before a script is executed.
        """

        for path in paths :
            if path:
                self.m_paths.append (path)

    def setASLimit (self, soft, hard = None) :

        """
        Set the active set limit for the executed command or script. This
        method is a shortcut to the L{setLimit} method.

        @type   soft    : Integer
        @param  soft    : Active set limit in bytes
        @type   hard    : Integer
        @param  hard    : Active set limit in bytes, defaults to soft limit
        """

        self.setLimit (resource.RLIMIT_AS, soft, hard)

    def setCPULimit (self, soft, hard = None) :

        """
        Set the CPU limit for the executed command or script. This
        method is a shortcut to the L{setLimit} method.

        @type   soft    : Integer
        @param  soft    : Soft CPU limit in seconds
        @type   hard    : Integer
        @param  hard    : Hard CPU limit in seconds, defaults to soft limit
        """

        self.setLimit (resource.RLIMIT_CPU, soft, hard)

    def setTraceback (self, traceback) :

        """
        Set the traceback mode. Currently should be

          - I{html} for a formatted HTML traceback
          - I{text} for a text traceback
          - otherwise a minimal text traceback is generated

        @type   traceback : String
        @param  traceback : Traceback mode
        """

        self.m_traceback = traceback

    def setTestName (self, testName) :

        """
        Set a test name. This is mainly useful for tests, will be passed
        through in headers and can be logged elsewhere.

        @type   testName: String
        @param  testName: Test name
        """

        self.m_testName = testName

    def setHeaders (self, setter) :

        """
        Set HTTP headers. This is factored out as a separate routine for
        ease of testing.

        @type   setter  : Closure or function
        @param  setter  : Callable to set header
        """

        if self.m_user       is not None :
            setter ('x-setuser',    self.m_user     )
        if self.m_group      is not None :
            setter ('x-setgroup',   self.m_group    )
        if self.m_traceback  is not None :
            setter ('x-traceback',  self.m_traceback)
        if self.m_scraperID  is not None :
            setter ('x-scraperid',  self.m_scraperID)
        if self.m_urlquery   is not None :
            setter ('x-urlquery',   self.m_urlquery )
        if self.m_testName   is not None :
            setter ('x-testname',   self.m_testName )
        if self.m_runID      is not None :
            setter ('x-runid',      self.m_runID    )
        if self.m_cache      is not None :
            setter ('x-cache',      self.m_cache    )
        if self.m_language   is not None :
            setter ('x-language',   self.m_language )

        for resource, limit in self.m_limits.items() :
            setter ('x-setrlimit-%d' % resource, '%s,%s' % (limit[0], limit[1]))

        envs = self.m_environment.items()
        for envn in range(len(envs)) :
            setter ('x-setenv-%d' % envn, '%s=%s' % (envs[envn][0], envs[envn][1]))

        for site in range(len(self.m_allowed )) :
            setter ('x-addallowedsite-%d' % site, self.m_allowed [site])

        for site in range(len(self.m_blocked )) :
            setter ('x-addblockedsite-%d' % site, self.m_blocked [site])

        for path in range(len(self.m_paths   )) :
            setter ('x-paths-%d'          % path, self.m_paths   [path])

    def call (self, stream = False) :

        """
        Call the dispatcher to execute the command or script. This is an
        internal method would not normally be called directly.

        @type   stream  : Bool
        @param  stream  : Return object for streamed data
        @rtype      : String
        @return     : Output from command or script
        """

        import urllib
        import urllib2

        self.m_swlog.log         (self.m_scraperID, self.m_runID, 'F.CALL')

        data = urllib.urlencode  (self.m_parameters)
        req  = urllib2.Request   ('http://%s/%s' % (self.m_dispatcher, self.m_path), data)

        self.setHeaders (req.add_header)

        try :
            resp = urllib2.urlopen   (req)
        except :
            self.m_error = str(sys.exc_info()[1])
            return None

        #  If streaming mode is requested, then return the response object,
        #  so the caller can read from it. Otherwise, read the entire result
        #  and return that.
        #
        wrapper = FireWrapper(resp)
        if stream :
            return wrapper

        return wrapper.read()

    def command (self, command, stream = False) :

        """
        Execute a specified command. The command is passed to the
        I{subprocess.Popen} function.

        @type   command : String
        @param  command : Command to execute
        @type   stream  : Bool
        @param  stream  : Return object for streamed data
        @rtype      : String
        @return     : Output from command
        """

        self.setPath      ('Command')
        self.setParameter ('command', command)
        return self.call  (stream)

    def execute (self, script, stream = False) :

        """
        Execute a specified script.

        @type   command : String
        @param  command : Text of script to execute
        @type   stream  : Bool
        @param  stream  : Return object for streamed data
        @rtype      : String
        @return     : Output from script
        """

        self.setPath      ('Execute')
        self.setParameter ('script', script)
        return self.call  (stream)

