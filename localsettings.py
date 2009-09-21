# local configurations for your computer.  Do not commit to SVN unless saved under 'localsettings.py-insvn'

DATABASE_ENGINE     = 'mysql'       # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME       = 'scraperwiki' # Or path to database file if using sqlite3.
DATABASE_USER       = 'scraperwiki'   # Not used with sqlite3.
DATABASE_PASSWORD   = 'troggle'         # Not used with sqlite3.
URL_ROOT            = '/sw/'           # prefix for URLs to run not at top level of domain

HOME_DIR            = "/home/scraperwiki/"           # the parent directory of SCRAPERWIKI_DIR
SCRAPERWIKI_DIR     = '/home/scraperwiki/web/'       # top level directory of the installation
READINGS_DIR        = '/home/scraperwiki/readings/'  # directory containing the cached webpages
SMODULES_DIR        = '/home/scraperwiki/scrapers/'

