
# 
# In process of trying to get dynamic django tables to work
# 



import settings 
from django.db import connection
from django.core import management
import codewiki.models as models

import sys
from django.core.management import color, sql
from detectors.scraperutils import GetDetectings
from django.db import models as dmodels



# local definition of this model
class FireSteem(dmodels.Model):
    firename   = dmodels.CharField(max_length=200)  

    class Meta:
        app_label = "codewiki"
    
    def __unicode__(self):
        return "firename: %s" % (self.firename)


# this should drop the associated table for the above and reload it
def MakeModels():
    tables = connection.introspection.table_names()
    print tables
    print dir(connection.creation.sql_create_model)
    print dir(dmodels)
    
    #settings.INSTALLED_APPS.append("collectors.londonfire")
    print "apps", map(lambda s: s.__name__ , dmodels.get_apps())
    
    cursor = connection.cursor()
    style = color.no_style()
    app = dmodels.get_app("codewiki")
    print "aaa", [app]
    statements = sql.sql_create(app, style)
    for ssql in statements:
        print ssql
        cursor.execute(ssql)
    #print help(sql.custom_sql_for_model)
    #print sql.custom_sql_for_model(models.Reading, style)
    print sql.custom_sql_for_model(FireSteem, style)
    #for sql in statements:
    #    cursor.execute(sql)


# runs the chosen scraper against all readings and produces detectings
# these partial results would otherwise be cached in a (key-value) database for slicker access
if "collect" in sys.argv:
    detector = models.ScraperScript.objects.get(dirname="detectors", modulename="londonfire")
    for detection in detector.detection_set.filter(status="parsed"):
        keyvalues = eval(detection.result)
        print keyvalues
        continue
        
        if "firefighters" not in keyvalues or "startdate" not in keyvalues:
            continue
        print "ii", keyvalues
        dkeys = ("title", "calleddate", "firefighters", )
        dvalues = (keyvalues["title"], keyvalues["startdate"], keyvalues["firefighters"])
        lcmd = "SELECT * FROM londonfire WHERE %s" % (" AND ".join(["%s='%s'" % (dkey, dvalue)  for dkey, dvalue in zip(dkeys, dvalues)]))
        cursor.execute(lcmd)
        if not cursor.fetchall():
            scmd = "REPLACE INTO londonfire (%s) VALUES (%s)" % (",".join(dkeys), ",".join(["'%s'"%dvalue  for dvalue in dvalues]))
            cursor.execute(scmd)
            print scmd
            nnew += 1
        else:
            nfound += 1
    print "Records found:", nfound, " new:", nnew

    
    
#showstuff()

