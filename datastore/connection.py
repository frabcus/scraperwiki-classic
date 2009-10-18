#!/usr/bin/env python
# encoding: utf-8

import sys
import ConfigParser
import MySQLdb

"""
Handles the database connection
"""

def load_config():
  """
  Create a ConfigParser, open ``config.cfg`` and return it.
    
  """
  config = ConfigParser.ConfigParser()
  config.readfp(open('config.cfg'))
  return config

def connect():
  """
  Open a MySQLdb connection with the information in config.cfg and return a
  connection object.
  """
  
  config = load_config()

  db = MySQLdb.connect(
    host=config.get('mysql', 'host'), 
    user=config.get('mysql', 'user'), 
    passwd=config.get('mysql', 'passwd'),
    db=config.get('mysql', 'db'),
    )
 
  return db.cursor()
  
 
if __name__ == "__main__":
  connect()  
