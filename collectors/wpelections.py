from django.db import models
import settings 
from django.db import connection
from django.core import management
import codewiki.models

import sys, re
from django.core.management import color, sql
from MySQLdb import escape_string


def showstuff():
    style = color.color_style()
    print "tablenames", connection.introspection.table_names()
    app = metroscope.codewiki.models
    print "sqlcreatecall", sql.sql_create(app, style)


# needs to drop and remake a set of tables used by the user
# does this involve making a module that is included by models.py?
# look up clean way of making these on the fly to be used in the observers
def MakeModels():
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)

    # "IF EXISTS" doesn't work to avoid exceptions
    try:
        cursor.execute("DROP TABLE IF EXISTS candidate")  
    except:
        print "exception: IF table EXISTS feature doesn't work"

    candidatefields = ["id integer AUTO_INCREMENT NOT NULL PRIMARY KEY", 
                      "election varchar(200) NOT NULL",
                      "year varchar(20) NULL",
                      "candidate varchar(200)",
                      "party varchar(200) NOT NULL",
                      "votes integer", 
                      "winner boolean", 
                      "constituency varchar(200) NOT NULL", 
                      ]
    cursor.execute("CREATE TABLE candidate (%s)" % ",".join(candidatefields))


def q(s):
    return "'%s'" % escape_string(s)

# runs the chosen scraper against all readings and produces detectings
# these partial results would otherwise be cached in a (key-value) database for slicker access
if "collect" in sys.argv:
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    detector = codewiki.models.ScraperScript.objects.get(dirname="detectors", modulename="wpconstituencies")
    i = 0
    cursor.execute("DELETE FROM candidate")
    for detection in detector.detection_set.filter(status="parsed"):
        for kv in detection.contents():
            if kv["type"] == "election":
                pass
            if kv["type"] == "candidate":
                myear = re.search("(\d\d\d\d)", kv["election"])
                year = myear and myear.group(1) or "0000"
                dkeys = ("election", "year", "party", "votes", "constituency")
                dvalues = (q(kv["election"]), q(year), q(kv["party"]), str(kv["votes"] or 0), q(kv["constituency"])) 
                scmd = "REPLACE INTO candidate (%s) VALUES (%s)" % (",".join(dkeys), ",".join(dvalues))
                i += 1
                if (i % 10) == 0:
                    print scmd
                cursor.execute(scmd)


        
    
#showstuff()

