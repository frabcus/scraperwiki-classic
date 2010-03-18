#!/bin/python
"""
A script to launch the orbited server as a deamon.

"""

import os
import sys
import time
from optparse import OptionParser


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--vardir", dest="varDir", action="store", 
        type='str', help="Port that receives connections from orbited.",  
        default='/tmp', metavar="Directory to log to")

    parser.add_option("-k", "--kill", dest="kill", action="store_true")

    (options, args) = parser.parse_args()
    
    varDir = options.varDir
    
    stdout_file_path = varDir + '/orbited'
    stdin_file_path = '/dev/null'
    pid_file_path = varDir + '/orbited.pid'
    
    if options.kill:
        pf = open (pid_file_path, 'r')
        print pf.read()
        pf.close  ()
        
        # os.kill(self.running.pid, signal.SIGKILL)
        
    
    if os.fork() == 0:
        os .setsid()
        sys.stdin  = open (stdin_file_path)
        sys.stdout = open (stdout_file_path, 'w')
        sys.stderr = sys.stdout
        if os.fork() == 0 :
            ppid = os.getppid()
            while ppid != 1 :
                time.sleep (1)
                ppid = os.getppid()
        else :
            os._exit (0)
    else :
        os.wait()
        sys.exit (1)

    pf = open (pid_file_path, 'w')
    pf.write  ('%d\n' % os.getpid())
    pf.close  ()
        
    # print os.fork()