#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import MySQLdb
import settings

"""
Handles the database connection
"""

class Connection(object):

    def __init__(self):
        self.is_connected = False


    def __test(self):
        print "worked"

    def connect(self):
        """
        Open a MySQLdb connection with the information in config.cfg and return a
        connection object.
        """

        if not self.is_connected:
            try :
                self.db = MySQLdb.connect(
                  host=settings.DATASTORE_DATABASE_HOST,
                  user=settings.DATASTORE_DATABASE_USER, 
                  passwd=settings.DATASTORE_DATABASE_PASSWORD,
                  db=settings.DATASTORE_DATABASE_NAME,
                  )
                self.is_connected = True
            except :
                raise Exception("Unable to connect to datastore")

        return self.is_connected

    def cursor(self):
        if not self.is_connected:
            self.connect()
        return self.db.cursor()
  
    
if __name__ == "__main__":
  c = Connection()
  print dir(c)
  c.connect()
