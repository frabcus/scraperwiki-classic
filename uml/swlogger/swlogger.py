import os, logging, logging.handlers

class SWLogger(object):
    """
    SWLogger is a wrapper around the default python logging framework that 
    simplifies the setup of the logging by processing it all in the constructor
    before forwarding calls to info(), debug() etc to the newly created logger.
    
    Whilst support for changing the logging level exists based on a name ( one 
    of 'critical', 'error', 'info', 'warning', 'debug' ) there is no support 
    for changing the handlers themselves as runtime.
    """
    
    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    LEVELS = {
        'critical': logging.CRITICAL,
        'error'   : logging.ERROR,        
        'info'    : logging.INFO,
        'warning' : logging.WARNING,
        'debug'   : logging.DEBUG,
    }
    
    
    def __init__(self, name='sw', level='critical'):
        """
        Constructor creates and configures the logging framework for use 
        by the caller.  Uses 'name' to set the logging filename and level
        to specify the initial logging level.
        """
        assert level in SWLogger.LEVELS
        assert name is not None
        
        super(SWLogger,self).__init__()

        logging.basicConfig( format=SWLogger.FORMAT )
        self.logger = logging.getLogger( name )
        self.setLevel( level )
        
        # Setup the handler and the formatting that we want for the handler
        outputfile = os.path.join( '../var/log/', '%s.log' % name )        
        handler = logging.handlers.RotatingFileHandler( outputfile, 
                                                        maxBytes=10485760, 
                                                        backupCount=5 )
        formatter = logging.Formatter( SWLogger.FORMAT )
        handler.setFormatter( formatter )

        # Setup critical errors to be sent via email to 
        # developers@scraperwiki.com
        to_emails = ['developers@scraperwiki.com']
        smtp_handler = logging.handlers.SMTPHandler( ( 'localhost', 25, ), 
                                                     'server@scraperwiki.com', 
                                                     to_emails, 
                                                    'ScraperWiki error in %s' % name )        
        smtp_handler.setLevel( logging.CRITICAL )
        smtp_handler.setFormatter( formatter )

        # Add both of our handlers
        self.logger.addHandler( smtp_handler ) 
        self.logger.addHandler( handler ) 
        
        
    def setLevel(self, name):
        """
        Sets the logging level by looking up the value provided in SWLogger.LEVELS 
        and defaulting to error if not found.
        """
        assert name in SWLogger.LEVELS
        self.logger.setLevel( SWLogger.LEVELS.get( name,logging.ERROR ) )                

        
    def __getattribute__(self,name):
        """
        If the attribute being fetched is one that we need to forward to the 
        Logger then forward it, otherwise use the local attribute instead.
        """        
        if name in ['info', 'debug', 'critical', 'warning']:
            return getattr( self.logger, name )
        return super(SWLogger,self).__getattribute__( name )
    
    
if __name__ == '__main__':
    s = SWLogger( level='info' )
    s.info( 'Testing the info level' )
    s.critical( 'Errrk' ) # Should send emails
    
    s.setLevel( 'critical' ) 
    s.info( 'Should never show' )    
    
    s.setLevel( 'info' ) 
    s.info( 'Should show now' )        