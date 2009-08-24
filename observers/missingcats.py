import settings 
from django.db import connection
import sys

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


if "render" in sys.argv:
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT missingcat, missingtime, missingplace FROM missingcat")
    
    print "<h1>Missing cats by month</h1>"
    monthcats = [0] * 13
    for missingcat in cursor.fetchall():
        monthcats[missingcat[1].month] += 1
        
    print "<table>"
    print "<tr><th>Month</th><th>Number of cats missing</th></tr>"
    for i in range(1, 13):
        print "<tr><td>%s</td><td>%d</td></tr>" % (months[i - 1], monthcats[i])
    print "</table>"
    

