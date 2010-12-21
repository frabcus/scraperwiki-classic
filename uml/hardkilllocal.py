#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

# Find all lost processes in the system and kill them.  
# Necessary when killlocal might have hit errors during execution

import os
for t in ['twister', 'www/scraperwiki/uml']:
    for s in os.popen('ps -AF | grep %s' % t).readlines():
        try:
            print "killing", s
            os.kill(int(s.split()[1]), 9)
        except:
            print "    missing"
        


