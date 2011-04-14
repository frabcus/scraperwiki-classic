import sys
import resource
import string
import time
import inspect
import os
import hashlib
import ConfigParser
import urllib
import urllib2
import cStringIO
import socket

try:
    import simplejson as json
except:
    import json

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


        self.m_dispatcher_host  = None
        self.m_dispatcher_port  = None
        self.m_parameters  = {}
        self.m_environment = {}
        self.m_user        = None
        self.m_draft       = False
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

        # this runID is incredibly ugly, unnecessarily long, and will be prepended with "draft" for draft modes
        # also gets "fromfrontend" prepended when the running of a script from the webpage
        s = hashlib.sha1()
        s.update(str(os.urandom(16)))
        s.update(str(os.getpid (  )))
        s.update(str(time.time (  )))
        self.m_runID       = '%.6f_%s' % (time.time(), s.hexdigest())

        self.soc_file = None


    def error (self) :

        """
        Return error string

        @rtype      : String
        @return     : Error string or None if no error
        """

        return self.m_error

    def setDispatcherHost(self, dispatcher_host) :

        """
        Set the dispatcher address.

        @type   dispatcher_host  : String
        @param  dispatcher_host  : Dispatcher address
        """

        self.m_dispatcher_host = dispatcher_host

    def setDispatcherPort (self, dispatcher_port) :

        """
        Set the dispatcher port.

        @type   dispatcher  : String
        @param  dispatcher  : Dispatcher port
        """

        self.m_dispatcher_port = dispatcher_port

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

    def setDraft (self, draft) :

        """
        Set user that command or script will execute as

        @type   user    : String
        @param  user    : User name
        """

        self.m_draft = draft
    
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

        self.setDispatcherHost(self.m_conf.get('dispatcher', 'host'))
        self.setDispatcherPort(self.m_conf.getint('dispatcher', 'port'))

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
            lrunID = self.m_runID
            if self.m_draft:
                lrunID = "draft|||%s" % lrunID
            setter ('x-runid',      lrunID          )
        
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

    def _call(self, path, command=None, script=None):

        """
        Call the dispatcher to execute the command or script. This is an
        internal method would not normally be called directly.
        """

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            soc.connect((self.m_dispatcher_host, self.m_dispatcher_port))
        except:
            return self

        if command:
            data = json.dumps({'command': command})
        elif script:
            data = json.dumps({'script': script})
        else:
            raise Exception("Either command or script parameters must be provided")

        soc.send('POST %s HTTP/1.1\r\n' % path)
        soc.send('Content-Length: %s\r\n' % len(data))
        soc.send('Connection: close\r\n')

        def add_header(x, y):
            soc.send("%s: %s\r\n" % (x, y))
        self.setHeaders(add_header)
        soc.send('\r\n')
        soc.send(data)

        self.soc_file = soc.makefile('r')
        status_line = self.soc_file.readline()
        if status_line.split(' ')[1] != '200':
            self.m_error = status_line.split(' ', 2)[2].strip()
            self.soc_file.close()
            return self

        while True: # Ignore the HTTP headers
            line = self.soc_file.readline()
            if line.strip() == "":
                break

        return self

    def __iter__(self):
        return self

    def next(self):
        if self.m_error:
            message = json.dumps({'message_type' : 'fail', 'content' : self.m_error})
            self.m_error = None
            return message
        elif self.soc_file and not self.soc_file.closed:
            line = self.soc_file.readline().strip()
            if line == '':
                self.soc_file.close()
                raise StopIteration
            else:
                return line
        else:
            raise StopIteration

    def command(self, command):

        """
        Execute a specified command. The command is passed to the
        I{subprocess.Popen} function.

        @type   command : String
        @param  command : Command to execute
        @rtype      : String
        @return     : Output from command
        """

        return self._call('/Command', command=command)

    def execute(self, script):

        """
        Execute a specified script.

        @type   command : String
        @param  command : Text of script to execute
        @rtype      : String
        @return     : Output from script
        """

        return self._call('/Execute', script=script)

