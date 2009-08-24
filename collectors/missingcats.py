from django.db import models
import settings 
from django.db import connection
from django.core import management
import metroscope.codewiki.models

import sys
from django.core.management import color, sql
from detectors.scraperutils import GetDetectings

# I am using raw SQL to get the job done.  
# Ideally we'd use the model and object creator from within Django somehow as the effective wrapper of the user-defined database tables
# Don't worry too much about making namespaces for each of the users.  
# The magic comes from everyone being forced into using the same namespace and therefore getting stuff to work in common

def showstuff():
    style = color.color_style()
    print "tablenames", connection.introspection.table_names()
    app = metroscope.codewiki.models
    print "sqlcreatecall", sql.sql_create(app, style)


# needs to drop and remake a set of tables used by the user
# does this involve making a module that is included by models.py?
# look up clean way of making these on the fly to be used in the observers
if "makemodel" in sys.argv:
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    #cursor.execute("DROP TABLE IF EXISTS missingcat")  # "if exists" doesn't work to avoid exceptions
    missingcatfields = [ "id integer AUTO_INCREMENT NOT NULL PRIMARY KEY", 
                     "missingcat varchar(200) NOT NULL",
                     "missingtime datetime NULL",
                     "missingplace longtext" ]
    cursor.execute("CREATE TABLE missingcat (%s)" % ",".join(missingcatfields))
    #sys.exit(0)
    #cursor.execute("REPLACE INTO missingcat (missingcat, missingtime, missingplace) VALUES ('tiddles', '2009-10-10', 'somewhere in bradford')")
    #cursor.execute("SELECT * FROM missingcat")
    #print cursor.fetchall()


# runs the chosen scraper against all readings and produces detectings
# these partial results would otherwise be cached in a (key-value) database for slicker access
if "collect" in sys.argv:
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    nnew, nfound = 0, 0
    for keyvalues in GetDetectings("detectors.missingcats"):
        dkeys = ("missingcat", "missingtime", "missingplace")
        dvalues = (keyvalues["title"], keyvalues["date"], keyvalues["description"])
        lcmd = "SELECT * FROM missingcat WHERE %s" % (" AND ".join(["%s='%s'" % (dkey, dvalue)  for dkey, dvalue in zip(dkeys, dvalues)]))
        cursor.execute(lcmd)
        if not cursor.fetchall():
            scmd = "REPLACE INTO missingcat (%s) VALUES (%s)" % (",".join(dkeys), ",".join(["'%s'"%dvalue  for dvalue in dvalues]))
            cursor.execute(scmd)
            nnew += 1
        else:
            nfound += 1
    print "Records found:", nfound, " new:", nnew
        
    
#showstuff()

