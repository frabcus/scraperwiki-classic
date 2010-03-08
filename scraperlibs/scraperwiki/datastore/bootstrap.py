#!/usr/bin/env python
# encoding: utf-8

"""
Does the initial loading of the databases.
"""

import ConfigParser
import connection
import sys
import os
import csv
sys.path.append('..')
import geo

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

def load_gb_postcodes():
    """ Loads royal mail's postcode database (postzon) and postcode sector data, converting eastings/northings to latlong """

    #get the location of the postzon file
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.split(__file__)[0] + 'config.cfg.local'))

    #open connection
    conn = connection.Connection()
    c = conn.cursor()

    #clear any existing data
    sql = "delete from postcode_lookup"
    c.execute(sql)

    #open the postzon file
    postzon_path = config.get('data', 'postzon_path')
    csv_reader = csv.reader(open(postzon_path))

    i = 0
    for row in csv_reader:
        if i > 0:

            #get the bits we want out of this row
            postcode = row[0].replace('  ', ' ') #remove the random extra place 
            easting = int(row[2].ljust(6, '0'))
            northing = int(row[3].ljust(6, '0'))
            country_code = 'GB'
            if postcode.startswith('BT'):
                latlng = geo.os_easting_northing_to_latlng(easting, northing, 'IE')
            else:    
                latlng = geo.os_easting_northing_to_latlng(easting, northing, 'GB')

            #insert into database
            sql = "insert into postcode_lookup (postcode, location, country_code) values ('%s', GeomFromText( ' POINT(%f %f) '), '%s')" % (postcode, latlng[0], latlng[1], country_code)    

            c.execute(sql)
        i = i + 1


    #close connection
    c.close()
      
if __name__ == "__main__":

    #get the method
    method = False
    if len(sys.argv) == 2:
        method = sys.argv[1]

    #work out what to run
    if method == 'kvschema':
        load_scheme()
    elif method == 'test_postcode':
        latlng = geo.gb_postcode_to_latlng('SW9 8JX')
        print latlng
    elif method == 'postcodes':        
        load_gb_postcodes()
    else:
        print "Argument needs to be one of:\n 'kvschema' - drops and create the kv database tables\n 'postcodes' - creates UK postcode tables and load data"