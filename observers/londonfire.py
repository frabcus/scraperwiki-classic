import settings 
import codewiki.models as models
from django.db import connection
import sys

 
if "render" in sys.argv:
    detector = models.ScraperScript.objects.get(dirname="detectors", modulename="londonfire")
    allkeyvalues = [ ]
    for detection in detector.detection_set.filter(status="parsed"):
        allkeyvalues.extend(eval(detection.result))
    print len(allkeyvalues)
    
    print "<h1>Fire Callouts</h1>"
    print "<table>"
    print "<tr><th>Date</th><th>Title</th><th>Number firefighters</th></tr>"
    for kv in allkeyvalues:
        print "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (kv.get("startdate"), kv.get("title"), kv.get("firefighters"))
    print "</table>"

    
if "Drender" in sys.argv:
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT title, firefighters, calleddate FROM londonfire ORDER BY calleddate")
    
    print "<h1>Fire Callouts</h1>"
        
    print "<table>"
    print "<tr><th>Date</th><th>Title</th><th>Number firefighters</th></tr>"
    n, nf = 0, 0
    for title, firefighters, calleddate in cursor.fetchall():
        print "<tr><td>%s</td><td>%s</td><td>%d</td></tr>" % (calleddate, title, firefighters)
        n = n + 1
        nf = nf + firefighters
    print "</table>"
    print '<h2>On average there were ', float(nf)/n, "firefighters called per scene</h2>"
    

