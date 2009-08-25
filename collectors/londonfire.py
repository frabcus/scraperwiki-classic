import settings 
from django.db import connection
from django.core import management
import codewiki.models as models

import sys
from django.core.management import color, sql
from detectors.scraperutils import GetDetectings
from django.db import models as dmodels
# I am using raw SQL to get the job done.  
# Ideally we'd use the model and object creator from within Django somehow as the effective wrapper of the user-defined database tables
# Don't worry too much about making namespaces for each of the users.  
# The magic comes from everyone being forced into using the same namespace and therefore getting stuff to work in common


# needs to drop and remake a set of tables used by the user
# does this involve making a module that is included by models.py?
# look up clean way of making these on the fly to be used in the observers
if "makemodel" in sys.argv:
    print "hi there"
    
    fields = {
            'first_name': dmodels.CharField(max_length=255),
            'last_name': dmodels.CharField(max_length=255),
            '__str__': lambda self: '%s %s' (self.first_name, self.last_name),
            }
    options = { 'ordering': ['last_name', 'first_name'], }
    admin_opts = {} 
    model = models.create_model('Person', fields,
                options=options,
                admin_opts=admin_opts,
                app_label='fake_app',
                module='fake_project.fake_app.no_models',
                )
    print len(model._meta.fields)
    sys.exit(0)
    models.make
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    #cursor.execute("DROP TABLE IF EXISTS londonfire")  # "if exists" doesn't work to avoid exceptions
    missingcatfields = [ "id integer AUTO_INCREMENT NOT NULL PRIMARY KEY", 
                     "title longtext", 
                     "firefighters integer",
                     "calleddate datetime NULL",
                     "missingplace longtext" ]
    cursor.execute("CREATE TABLE londonfire (%s)" % ",".join(missingcatfields))


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

