#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import ConfigParser
import MySQLdb

"""
Handles the database connection
"""

class Connection(object):
  
  
  def __load_config(self):
    """
    Create a ConfigParser, open ``config.cfg`` and return it.
    """

    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.split(__file__)[0] + '/config.cfg.local'))
    return config

  def __test(self):
    print "worked"
    
  def connect(self):
    """
    Open a MySQLdb connection with the information in config.cfg and return a
    connection object.
    """
  
    config = self.__load_config()

    db = MySQLdb.connect(
      host=config.get('mysql', 'host'), 
      user=config.get('mysql', 'user'), 
      passwd=config.get('mysql', 'passwd'),
      db=config.get('mysql', 'db'),
      )
 
    return db.cursor()
  
 
if __name__ == "__main__":
  c = Connection()
  print dir(c)
  c.connect()
