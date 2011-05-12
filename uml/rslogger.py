import os, logging, logging.handlers
import socket

FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LEVELS = {
    'debug'   : logging.DEBUG,    #10
    'info'    : logging.INFO,     #20
    'warning' : logging.WARNING,  #30
    'error'   : logging.ERROR,    #40
    'critical': logging.CRITICAL, #50
}

def getlogger(name, logfile, level='debug', toaddrs=[]):
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger(name)
    logger.setLevel(LEVELS[level])
    
    # Setup the handler and the formatting that we want for the handler
    handler = logging.handlers.RotatingFileHandler( logfile, maxBytes=10485760, backupCount=5 )
    formatter = logging.Formatter( FORMAT )
    handler.setFormatter( formatter )

    logger.addHandler( handler ) 
    
    # Setup critical errors to be sent via email to 
    # developers@scraperwiki.com
    if not toaddrs:
        #to_emails = ['developers@scraperwiki.com']
    
        smtp_handler = logging.handlers.SMTPHandler(maihost=('localhost', 25,), fromaddr='server@scraperwiki.com', 
                                                    toaddrs=toaddrs, subject='ScraperWiki error in %s' % name)
        smtp_handler.setLevel( logging.CRITICAL )
        smtp_handler.setFormatter( formatter )

        logger.addHandler( smtp_handler ) 
    
    
    return logger


def setLevel(logger, name):
    assert name in LEVELS
    logger.setLevel( LEVELS.get( name,logging.ERROR ) )

if __name__ == '__main__':
    s = getlogger( level='info' )
    s.info( 'Testing the info level' )
    s.critical( 'Errrk' ) # Should send emails
    
    setLevel(s, 'critical' ) 
    s.info( 'Should never show' )    
    
    setLevel(s, 'info' ) 
    s.info( 'Should show now' )        
    
