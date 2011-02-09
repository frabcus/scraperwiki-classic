import  time
import  ConfigParser
import  types
import sys

class SWLogger :

    """
    Logging code used by the UML subsystem (Dispatcher, Controller, Proxy)
    and the FireStarter module to log events,
    """

    def __init__ (self, config) :

        """
        Class constructor. Picks up database connection configuration.
        """

        if type(config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(config))
        else :
            conf = config

        self.m_host = conf.get ('swlogger', 'host'  )
        self.m_db   = conf.get ('swlogger', 'db'    )
        self.m_user = conf.get ('swlogger', 'user'  )
        self.m_passwd   = conf.get ('swlogger', 'passwd')
        self.m_mysql    = None

    def setHost (self, host) :

        """
        Explicitely set the host.

        @type   host    : String
        @param  host    : Database host name or IP address
        """

        self.m_host = host

    def connect (self) :

        """
        Connect to the logging database. If the host is not set then do not
        connect; in this event no logging takes place.
        """

        if self.m_host :
            import MySQLdb
            self.m_mysql    = MySQLdb.connect (host = self.m_host, db = self.m_db, user = self.m_user, passwd = self.m_passwd)

    def close (self) :

        """
        Close database connection.
        """
	if self.m_mysql:
	    self.m_mysql.close()
        self.m_mysql    = None

    def _functionId(self, nFramesUp):
        """ Create a string naming the function n frames up on the stack.
        """
        co = sys._getframe(nFramesUp+1).f_code
        return "%s (%s @ %d)" % (co.co_name, co.co_filename, co.co_firstlineno)

    def log (self, scraperid, runid, event, arg1 = None, arg2 = None) :

        """
        Log an event.

        @type   scraperid   : String
        @param  scraperid   : Scraper identifier
        @type   runid       : String
        @param  runid       : Run identifier
        @type   event       : String
        @param  event       : Event string
        @type   arg1        : Any
        @param  arg1        : First optional argument
        @type   arg2        : Any
        @param  arg2        : Second optional argument
        """

        if self.m_mysql :
            # Describe where we've been called from
            #arg2 = self._functionId(2)

            cursor = self.m_mysql.cursor()
            cursor.execute \
            (   """
                insert into log (scraperid, runid, pytime, event, arg1, arg2)
                       values   (%s, %s, %s, %s, %s, %s)
                """,
                [ scraperid, runid, time.time(), event, arg1, arg2 ]
            )

    def clean (self, runid) :

        """
        Remove all entries for a specified run identifier.

        @type   runid       : String
        @param  runid       : Run identifier
        """

        if self.m_mysql :

            cursor = self.m_mysql.cursor ()
            cursor.execute ("delete from log where runid = %s", [ runid ])
            
            
            
# To whom it may concern, the table definition is: 
#
"""CREATE TABLE `log` (
  `id` int(11) NOT NULL auto_increment,
  `stamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `scraperid` varchar(255) default NULL,
  `runid` varchar(255) default NULL,
  `pytime` varchar(31) default NULL,
  `event` varchar(255) default NULL,
  `arg1` text,
  `arg2` text,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=16857 DEFAULT CHARSET=latin1"""

