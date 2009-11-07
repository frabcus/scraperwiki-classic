#!/usr/bin/env python
# encoding: utf-8

"""
Does the initial loading of the databases.
"""

import connection
import sys

def load_scheme():
  """Excicutes the SQL in scheme.sql"""
  
  exit = "y"
  while exit.lower() != "n" or exit.lower() !="y":
    if len(exit) != 0 and exit.lower() != "y":
      print "%s IS NOT A VALID CHOICE" % exit.upper()
    exit = raw_input("""WARNING: 
        This will destroy any existing data that may be 
        in the database.  Do you want to continue?\n[N/y]:""")
    if len(exit) <= 0 or exit[0].lower() == "n":
      print "Exiting"
      sys.exit()
    elif exit.lower() == "y":
      print "dumping"
      conn = connection.Connection()
      c = conn.connect()
      f = open('scheme.sql', 'r')
      c.execute(f.read())
      c.close()
      
      conn = connection.Connection()
      c = conn.connect()
      c.execute("""INSERT INTO `sequences` VALUES(0);""")
      c.close()
      break
      
      
      
      
      
if __name__ == "__main__":
 load_scheme()