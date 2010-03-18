import	time

class SWLogger :

    """
    Logging code used by the UML subsystem (Dispatcher, Controller, Proxy)
    and the FireStarter module to log events,
    """

    def __init__ (self) :

        """
        Class constructor. Picks up database connection configuration.
        """

        import SWConfig
        self.m_host	= SWConfig.host
        self.m_db	= SWConfig.db
        self.m_user	= SWConfig.user
        self.m_passwd	= SWConfig.passwd
        self.m_mysql	= None

    def setHost (self, host) :

        """
        Explicitely set the host.

        @type	host	: String
	@param	host	: Database host name or IP address
        """

        self.m_host	= host

    def connect (self) :

        """
        Connect to the logging database. If the host is not set then do not
        connect; in this event no logging takes place.
        """

        if self.m_host :
            import MySQLdb
            self.m_mysql	= MySQLdb.connect (host = self.m_host, db = self.m_db, user = self.m_user, passwd = self.m_passwd)

    def close (self) :

        """
        Close database connection.
        """

        self.m_mysql	= None

    def log (self, scraperid, runid, event, arg1 = None, arg2 = None) :

        """
        Log an event.

        @type	scraperid	: String
	@param	scraperid	: Scraper identifier
        @type	runid		: String
	@param	runid		: Run identifier
        @type	event		: String
	@param	event		: Event string
        @type	arg1		: Any
	@param	arg1		: First optional argument
        @type	arg2		: Any
	@param	arg2		: Second optional argument
        """

        if self.m_mysql :

            cursor = self.m_mysql.cursor()
            cursor.execute \
    		(	"""
    			insert into log (scraperid, runid, pytime, event, arg1, arg2)
    			       values   (%s, %s, %s, %s, %s, %s)
    			""",
    			[ scraperid, runid, time.time(), event, arg1, arg2 ]
    		)

    def clean (self, runid) :

        """
        Remove all entries for a specified run identifier.

        @type	runid		: String
	@param	runid		: Run identifier
        """

        if self.m_mysql :

            cursor = self.m_mysql.cursor ()
            cursor.execute ("delete from log where runid = %s", [ runid ])
