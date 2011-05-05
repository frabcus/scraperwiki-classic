import ConfigParser
import hashlib
import types
import os
import string
import time
import datetime
import sqlite3
import signal
import base64
import shutil
import re
import sys

try   : import json
except: import simplejson as json

class Database :

    def createSchema (self) :

        cursor = self.m_db.cursor()
        cursor.execute ('select name from sqlite_master order by name')
        tables = [ row[0] for row in cursor.fetchall() ]
        print "TABLES", tables

        if 'items' not in tables :
            cursor = self.m_db.cursor()
            cursor.execute \
                (   '''
                    create table `items`
                    (
                        `item_id`         integer         not null,
                        `unique_hash`     varchar(32)     not null,
                        `scraper_id`      varchar(100)    not null,
                        `date`            datetime,
                        `latlng`          varchar(100),
                        `date_scraped`    datetime
                    )
                    '''
                )
        if 'sequences' not in tables :
            cursor = self.m_db.cursor()
            cursor.execute \
                (   '''
                    create table `sequences`
                    (
                        `id`              integer         not null
                    )
                    '''
                )
            cursor.execute \
                (   '''
                    insert into `sequences` (`id`) values (1)
                    '''
                )
        if 'kv' not in tables :
            cursor = self.m_db.cursor()
            cursor.execute \
                (   '''
                    create table `kv`
                    (
                        `item_id`         integer     not null,
                        `key`             text        not null,
                        `value`           blob        not null
                    )
                    '''
            )

    def __init__(self, ldataproxy):
        self.dataproxy = ldataproxy

    def connect (self, config, scraperID) :

        """
        Get a database connection.
        """

        self.m_db = None
        
        self.m_sqlitedbconn = None
        self.m_sqlitedbcursor = None
        self.authorizer_func = None  
        
        self.sqlitesaveinfo = { }  # tablename -> info

        if type(config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(config))
        else :
            conf = config

        self.m_dbtype = conf.get ('dataproxy', 'dbtype')
        self.m_resourcedir = conf.get('dataproxy', 'resourcedir')
        self.m_max_api_distance = conf.get('dataproxy', 'max_api_distance')

        if self.m_dbtype == 'mysql'   :
            try    :
                import MySQLdb
                self.m_db    = MySQLdb.connect \
                                (    host       = conf.get ('dataproxy', 'host'  ), 
                                     user       = conf.get ('dataproxy', 'user'  ), 
                                     passwd     = conf.get ('dataproxy', 'passwd'),
                                     db         = conf.get ('dataproxy', 'db'    ),
                                     charset    = 'utf8'
                                )
                self.m_place = '%s'
            except Exception, e :
                raise Exception("Unable to connect to old ScraperWiki MySQL key/value datastore: %s" % e)

        if self.m_dbtype == 'sqlite3' :
            try :
                import sqlite3
                dbname  = conf.get ('dataproxy', 'db')
                dbname  = dbname.replace ('%{scraperid}', scraperID)
                self.m_db  = sqlite3.connect (dbname)
                import math
                self.m_db.create_function ('sin',  1, lambda value : math. sin(float(value)))
                self.m_db.create_function ('cos',  1, lambda value : math. cos(float(value)))
                self.m_db.create_function ('asin', 1, lambda value : math.asin(float(value)))
                self.m_db.create_function ('acos', 1, lambda value : math.acos(float(value)))
                self.m_db.create_function ('pi',   0, lambda       : math.pi)
                self.m_place   = '?'
                self.createSchema ()
            except Exception, e :
                raise Exception("Unable to connect to ScraperWiki SQLite datastore: %s" % e)

        if self.m_db is None :
            raise Exception("Unrecognised datastore type '%s'" % dbtype)
        

    def fixPlaceHolder (self, query) :

        """
        Fix place holders in query. Usually this is a null operation, but is needed
        for testing since the SQLite3 driver uses the (more sensible and standard)
        ? character as placeholder.
        """

        if self.m_place == '%s' :
            return query
        return query.replace ('%s', self.m_place)

    def execute (self, query, values = None) :

        """
        Create a cursor and execute a query, returning the cursor as the result.
        """

        try:
            cursor = self.m_db.cursor()
            query  = self.fixPlaceHolder(query)
            cursor.execute(query, values)
            return cursor
        except Exception, ex:
            print "Error executing query:", ex
            print query
            print values
            raise ex

    def uniqueHash (self, unique, data) :

        """
        Return a hash value over the values of a set of unique keys.
        """

        #  Get values for the unique keys into a list, converted to strings and
        #  ordered by key name; these are then joined into a single string with
        #  a suitable separator, and then hashed.
        #
        ulist = []
        for key in set(unique) :
            try    : ulist.append (str(data[key]))
            except : ulist.append (data[key].encode('utf-8'))
        return hashlib.md5(string.join(ulist, '\0342\0211\0210\0342\0211\0210\0342\0211\0210')).hexdigest()

    def nextItemID (self) :

        """
        Get a new item identifier value.
        """

        #  This is separated out since the code is a bit different for
        #  testing with SQLite3
        #
        if self.m_dbtype == 'mysql'   :
            cursor = self.execute ('update `sequences` set `id` = last_insert_id(`id`+1)')
            result = cursor.lastrowid
            self.m_db.commit()
            return result
        if self.m_dbtype == 'sqlite3' :
            cursor = self.execute ('update `sequences` set `id` = `id` + 1')
            self.m_db.commit()
            return self.execute('select `id` from `sequences`').fetchone()[0]
        raise Exception("Unrecognised datastore type '%s'" % self.m_dbtype)


    def postcodeToLatLng (self, scraperID, postcode) :   

        postcode = postcode.upper().replace(' ', '')
        cursor   = self.execute ('select x(location), y(location) from `postcode_lookup` where `postcode` = %s', [ postcode ])
        try :
            result = cursor.fetchone()
            return [ True,  ( result[0], result[1] ) ]
        except :
            return [ False, 'Postcode not found' ]



    def save (self, scraperID, unique_keys, scraped_data, date = None, latlng = None) :

        """
        Save values into the datastore.
        """

        #  Sanity checks
        #
        if type(unique_keys ) not in [ types.ListType, types.TupleType ] :
            return [ False, 'Unique keys must be a list or a tuple' ]
        if type(scraped_data) not in [ types.DictType ] :
            return [ False, 'Data values must be a dictionary' ]
        if len (unique_keys ) == 0 :
            return [ False, 'At least one unique key must be provided' ]

        unique_s = set (unique_keys )
        data_s   = set (scraped_data)
        if not unique_s.issubset(data_s) :
            return [ False, 'Unique keys must be a subset of the data keys' ]


        # now doesn't do anything because the conversion of the key/values happens in scraperlibs/datastore
        insert_data = {}
        for key, value in scraped_data.items() :
            insert_data[key] = value

        if scraperID in [ None, '' ] :
            return  [ True, 'Data OK to save' ]

        #  Look for existing values via the unique hash on the values of the unique
        #  keys.
        #
        uhash  = self.uniqueHash (unique_keys, scraped_data)
        cursor = self.execute    ('select `item_id` from `items` where `scraper_id` = %s and `unique_hash` = %s', (scraperID, uhash))
        idlist = [ str(row[0]) for row in cursor.fetchall() ]

        #  Special case if more than one item was matched, which should actually
        #  never occur. If it does then just delete all key/value pairs and all
        #  items.
        #
        if len(idlist) >  1 :
            try:
                self.execute ('delete from `kv`    where `item_id` in (%s)' % string.join(idlist, ','))
                self.execute ('delete from `items` where `item_id` in (%s)' % string.join(idlist, ','))
            except:
                self.m_db.rollback()
            else:
                self.m_db.commit()
                

        #  If exactly one record matched then see if the other values have changed;
        #  if not then do nothing with the data and return "already exists", else
        #  update the values and return "updated". In either casse, update the lat/lng
        #  and date in the items record.
        #
        elif len(idlist) == 1:
            try:
                self.execute \
                    (   'update `items` set `date` = %s, `latlng` = %s, `date_scraped` = %s where `item_id` = %s',
                        (   date, latlng, time.strftime('%Y-%m-%d %H:%M:%S'), idlist[0] )
                    )

                extant_data = {}
                cursor = self.execute ('select `key`, `value` from `kv` where `item_id` = %s', ( idlist[0], ))
                for key, value in cursor.fetchall() :
                    extant_data[key] = value
                if extant_data == insert_data :
                    return [ True, 'Data record already exists' ]

                for key, value in insert_data.items() :
                    cursor = self.execute ('select 1 from `kv` where `item_id` = %s and `key` = %s', (idlist[0], key))

                    if cursor.rowcount == 0:
                        self.execute \
                            (    '''
                                 insert  into    `kv`
                                         (       `item_id`,
                                                 `key`,
                                                 `value`
                                         )
                                 values  (        %s, %s, %s
                                         )
                                 ''',
                                 (       idlist[0],
                                         key,
                                         value
                                 )
                            )
                    else :
                        self.execute \
                            (   '''
                                update  `kv`
                                set     `value`     = %s
                                where   `item_id`   = %s
                                and     `key`       = %s
                                ''',
                                [   value, idlist[0], key   ]
                            )
            except:
                self.m_db.rollback()
                return  [ False, 'Data record update failed' ]
            else:
                self.m_db.commit()
                return  [ True, 'Data record updated' ]

        #  New data to be inserted. Get a new item identifier and then insert
        #  the items record and the key-valuye pairs.
        #
        else:
            try:
                itemid = self.nextItemID ()

                self.execute \
                    (       '''
                            insert  into    `items`
                                    (       `item_id`,
                                            `unique_hash`,
                                            `scraper_id`,
                                            `date`,
                                            `latlng`,
                                            `date_scraped`
                                            )
                            values  (        %s, %s, %s, %s, %s, %s
                                    )
                            ''',
                            (       itemid,
                                    uhash,
                                    scraperID,
                                    date,
                                    latlng,
                                    time.strftime('%Y-%m-%d %H:%M:%S')
                            )
                    )

                for key, value in insert_data.items() :
                    self.execute \
                        (       '''
                                insert  into    `kv`
                                        (       `item_id`,
                                                `key`,
                                                `value`
                                        )
                                values  (        %s, %s, %s
                                        )
                                ''',
                                (       itemid,
                                        key,
                                        value
                                )
                        )
        
            except:
                self.m_db.rollback()
                return  [ False, 'Data record insert failed' ]
            else:
                self.m_db.commit()
                return  [ True, 'Data record inserted' ]


    def data_dictlist (self, scraperID, short_name, tablename, limit, offset, start_date, end_date, latlng) :
        
        # quick overload to redirect function to sqlite table if necessary
        if not tablename and short_name:   # decide if we are to use the sqlite table if available
            cursor = self.execute("select `item_id` from `items` where `scraper_id` = %s limit 1", (scraperID,))
            if not cursor.fetchall():
                tablename = "swdata"
        if tablename:
            result = self.sqlitecommand(scraperID, "fromfrontend", short_name, "execute", "select * from main.`%s` limit ? offset ?" % tablename, (limit, offset))
            if "error" in result:
                return [ False, result["error"] ]
            return [True, [ dict(zip(result["keys"], d))  for d in result["data"] ] ]
                
            
        qquery  = [ "select `items`.`item_id` as `item_id`" ]
        qparams = []

        if latlng is not None :
            qquery .append(", ((acos(sin(%s * pi() / 180) * sin(abs(substr(`items`.`latlng`, 1, 20)) * pi() / 180) + cos(%s * pi() / 180) * cos(abs(substr(`items`.`latlng`, 1, 20)) * pi() / 180) * cos((%s - abs(substr(`items`.`latlng`, 21, 41))) * pi() / 180)) * 180 / pi()) * 60 * 1.1515 * 1.609344) as distance")
            qparams.append(latlng[0])
            qparams.append(latlng[0])
            qparams.append(latlng[1])

        qquery .append("from `items`")

        # add the where clause
        #
        qquery .append("where `items`.`scraper_id` = %s")
        qparams.append(scraperID)

        if start_date is not None and end_date is not None :
            qquery .append("and `items`.`date` >= %s")
            qparams.append(start_date)
            qquery .append("and `items`.`date` <  %s")
            qparams.append(end_date)

        if latlng :
            qquery .append("and `items`.`latlng` is not null")            
            qquery .append("having distance < %s" )
            qparams.append(self.m_max_api_distance)            
            qquery .append("order by distance asc")
        else :
            qquery .append("order by `date_scraped` desc")

        qquery .append("limit %s,%s")
        qparams.append(offset)
        qparams.append(limit)

        cursor = self.execute (" ".join(qquery), tuple(qparams))
        item_idlist = cursor.fetchall ()

        allitems = [ ]
        for item_idl in item_idlist :
            
            #  get the item ID and create an object for the data to live in
            #
            item_id = item_idl[0]
            rdata = { }

            #  add distance if present
            #
            if len (item_idl) > 1:
                rdata['distance'] = item_idl[1]

            # header records
            #
            cursor = self.execute ("select `date`, `latlng`, `date_scraped` from `items` where `item_id` = %s", (item_id,))
            item   = cursor.fetchone()
            
            if item[0] is not None : rdata["date"        ] = str(item[0])           
            if item[2] is not None : rdata["date_scraped"] = str(item[2])

            #  put the key values in
            #
            cursor = self.execute("select `key`, `value` from `kv` where `item_id` = %s", (item_id,))
            for key, value in cursor.fetchall() :
                rdata[key] = value

            #  over-ride any values with latlng (we could break it into two values) (may need to wrap in a try to protect)
            #
            if item[1] is not None :
                try:
                    rdata["latlng"] = tuple(map(float, item[1].split(",")))
                except:
                    pass # If the data in the latlng column doesn't convert ignore it
        
            allitems.append (rdata)

        return [ True, allitems ]

    def clear_datastore(self, scraperID, short_name):
        self.execute("delete kv, items from kv join items on kv.item_id = items.item_id where scraper_id = %s", (scraperID,))
        self.m_db.commit()
            
        scraperresourcedir = os.path.join(self.m_resourcedir, short_name)
        scrapersqlitefile = os.path.join(scraperresourcedir, "defaultdb.sqlite")
        if os.path.isfile(scrapersqlitefile):
            deletedscrapersqlitefile = os.path.join(scraperresourcedir, "DELETED-defaultdb.sqlite")
            shutil.move(scrapersqlitefile, deletedscrapersqlitefile)
            
        return [ True, None ]

    def datastore_keys (self, scraperID) :
        result = []
        cursor = self.execute("select distinct `kv`.`key` from `items` inner join `kv` on `kv`.`item_id` = `items`.`item_id` where `items`.`scraper_id` = %s", (scraperID,))
        result = [ record[0] for record in cursor.fetchall() ]
        return [ True, result ]

    def data_search (self, scraperID, key_values, limit, offset) :   
        qquery  = [ "select `items`.`item_id`, count(`items`.`item_id`) as `item_count` from `items` inner join `kv` on `items`.`item_id` = `kv`.`item_id` where `items`.`scraper_id` = %s" ]
        qparams = [ scraperID ]

        filters = []
        for key_value in key_values:
            filters.append ("( `kv`.`key` = %s and `kv`.`value` = %s)" )
            qparams.append (key_value[0])
            qparams.append (key_value[1])

        qquery .append ("and (%s)" % " or ".join(filters))
        qquery .append ("group by `items`.`item_id`")
        qquery .append ("having `item_count` = %s")
        qparams.append (len(key_values))
        
        qquery .append ("limit %s,%s")
        qparams.append (offset)
        qparams.append (limit)

        #execute
        cursor = self.execute(" ".join(qquery), tuple(qparams))
        item_idlist = cursor.fetchall()

        allitems = [ ]
        for item_idl in item_idlist:

            #get the item ID and create an object for the data to live in
            item_id = item_idl[0]
            rdata = { }

            #add distance if present
            if len(item_idl) > 1:
                rdata['distance'] = item_idl[1]

            # header records
            cursor = self.execute("SELECT `date`, latlng, `date_scraped` FROM items WHERE item_id=%s", (item_id,))
            if cursor is None :
                continue  #TODO: raise an exception 
            item = cursor.fetchone()

            if item[0]:
                rdata["date"] = str(item[0])
            if item[2]:
                rdata["date_scraped"] = str(item[2])

            # put the key values in
            cursor = self.execute("select `key`, `value` from `kv` where `item_id` = %s", (item_id,))
            for key, value in cursor.fetchall():
                rdata[key] = value

            # over-ride any values with latlng (we could break it into two values) (may need to wrap in a try to protect)
            if item[1]:
                rdata["latlng"] = tuple(map(float, item[1].split(",")))
            else:
                rdata.pop("latlng", None)  # make sure this field is always a pair of floats

            allitems.append(rdata)

        return [ True, allitems ]


    # general single file sqlite access
    # the values of these fields are safe because from the UML they are subject to an ident callback, 
    # and from the frontend they are subject to a connection from a particular IP number
    def sqlitecommand(self, scraperID, runID, short_name, command, val1, val2):
        #print "XXXXX", (command, runID, val1, val2, self.m_sqlitedbcursor, self.m_sqlitedbconn)
        
        def authorizer_readonly(action_code, tname, cname, sql_location, trigger):
            #print "authorizer_readonly", (action_code, tname, cname, sql_location, trigger)
            readonlyops = [ sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_DETACH, 31 ]  # 31=SQLITE_FUNCTION missing from library.  codes: http://www.sqlite.org/c3ref/c_alter_table.html
            if action_code in readonlyops:
                return sqlite3.SQLITE_OK
            if action_code == sqlite3.SQLITE_PRAGMA:
                if tname in ["table_info", "index_list", "index_info"]:
                    return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        
        def authorizer_attaching(action_code, tname, cname, sql_location, trigger):
            #print "authorizer_attaching", (action_code, tname, cname, sql_location, trigger)
            if action_code == sqlite3.SQLITE_ATTACH:
                return sqlite3.SQLITE_OK
            return authorizer_readonly(action_code, tname, cname, sql_location, trigger)
        
        def authorizer_writemain(action_code, tname, cname, sql_location, trigger):
            #print "authorizer_writemain", (action_code, tname, cname, sql_location, trigger)
            if sql_location == None or sql_location == 'main':  
                return sqlite3.SQLITE_OK
            return authorizer_readonly(action_code, tname, cname, sql_location, trigger)
            
                    # apparently not able to reset authorizer function after it has been set once, so have to redirect this way
        def authorizer_all(action_code, tname, cname, sql_location, trigger):
            #print "authorizer_all", (action_code, tname, cname, sql_location, trigger)
            return self.authorizer_func(action_code, tname, cname, sql_location, trigger)


        if not runID:
            return {"error":"runID is blank"}
            
        if runID[:12] == "fromfrontend":
            self.authorizer_func = authorizer_readonly
        
                # ideally this would be a type that prevented write types onto the database
                # may need to copy to a temporary file or find a way to convert to a :memory: object
        elif runID[:8] == "draft|||" and short_name:
            self.authorizer_func = authorizer_readonly
        
        else:
            self.authorizer_func = authorizer_writemain
            
        if command == "downloadsqlitefile":
            scraperresourcedir = os.path.join(self.m_resourcedir, short_name)
            scrapersqlitefile = os.path.join(scraperresourcedir, "defaultdb.sqlite")
            lscrapersqlitefile = os.path.join(short_name, "defaultdb.sqlite")
            if not os.path.isfile(scrapersqlitefile):
                return {"status":"No sqlite database"}
            
            result = { "filename":lscrapersqlitefile, "filesize": os.path.getsize(scrapersqlitefile) }
            if val2 == 0:
                return result
            
            fin = open(scrapersqlitefile, "rb")
            if val1:
                fin.seek(val1)
                result["seek"] = val1
            else:
                result["seek"] = 0
            
            if val2:
                content = fin.read(val2)
            else:
                content = fin.read()
            result["length"] = len(content)
            result["content"] = base64.encodestring(content)
            result['encoding'] = "base64"
            fin.close()
            
            return result
            
            
            # make a new directory and connection if not seen anywhere (unless it's draft)
        if not self.m_sqlitedbconn:
            if short_name:
                scraperresourcedir = os.path.join(self.m_resourcedir, short_name)
                if not os.path.isdir(scraperresourcedir):
                    if command == "datasummary":
                        return {"status":"No sqlite database"}   # don't make one if we're just requesting a summary
                    os.mkdir(scraperresourcedir)
                scrapersqlitefile = os.path.join(scraperresourcedir, "defaultdb.sqlite")
                self.m_sqlitedbconn = sqlite3.connect(scrapersqlitefile)
            else:
                self.m_sqlitedbconn = sqlite3.connect(":memory:")   # draft scrapers make a local version
            self.m_sqlitedbconn.set_authorizer(authorizer_all)
            self.m_sqlitedbcursor = self.m_sqlitedbconn.cursor()
        
        if command == "execute":
            try:
                bstreamchunking = val2 and not re.search("\?", val1) and type(val2) in [list, tuple] and val2[0] == "streamchunking"
                    # this causes the process to entirely die after 10 seconds as the alarm is nowhere handled
                signal.alarm (30)  # should use set_progress_handler !!!!
                if val2 and not bstreamchunking:
                    self.m_sqlitedbcursor.execute(val1, val2)  # handle "(?,?,?)", (val, val, val)
                else:
                    self.m_sqlitedbcursor.execute(val1)
                signal.alarm (0)
                
                keys = self.m_sqlitedbcursor.description and map(lambda x:x[0], self.m_sqlitedbcursor.description) or []
                if not bstreamchunking:
                    return {"keys":keys, "data":self.m_sqlitedbcursor.fetchall()} 
                
                while True:
                    data = self.m_sqlitedbcursor.fetchmany(val2[1])
                    arg = {"keys":keys, "data":data} 
                    if len(data) < val2[1]:
                        return arg
                    arg["moredata"] = True
                    self.dataproxy.connection.send(json.dumps(arg) + '\n')  # push it out

            
            except sqlite3.Error, e:
                signal.alarm (0)
                return {"error":"sqlite3.Error: "+str(e)}
                
        if command == "datasummary":
            self.authorizer_func = authorizer_readonly
            tables = { }
            try:
                for name, sql in list(self.m_sqlitedbcursor.execute("select name, sql from sqlite_master where type='table'")):
                    tables[name] = {"sql":sql}
                    if val1 != "count":
                        self.m_sqlitedbcursor.execute("select * from `%s` order by rowid desc limit ?" % name, ((val1 == None and 10 or val1),))
                        if val1 != 0:
                            tables[name]["rows"] = list(self.m_sqlitedbcursor)
                        tables[name]["keys"] = map(lambda x:x[0], self.m_sqlitedbcursor.description)
                    tables[name]["count"] = list(self.m_sqlitedbcursor.execute("select count(1) from `%s`" % name))[0][0]
                    
            except sqlite3.Error, e:
                return {"error":"sqlite3.Error: "+str(e)}
            
            result = {"tables":tables}
            if short_name:
                scraperresourcedir = os.path.join(self.m_resourcedir, short_name)
                scrapersqlitefile = os.path.join(scraperresourcedir, "defaultdb.sqlite")
                if os.path.isfile(scrapersqlitefile):
                    result["filesize"] = os.path.getsize(scrapersqlitefile)
            return result
        
        if command == "attach":
            if self.authorizer_func == authorizer_writemain:
                self.m_sqlitedbconn.commit()  # otherwise a commit will be invoked by the attaching function
            self.authorizer_func = authorizer_attaching
            try:
                attachscrapersqlitefile = os.path.join(self.m_resourcedir, val1, "defaultdb.sqlite")
                self.m_sqlitedbcursor.execute('attach database ? as ?', (attachscrapersqlitefile, val2 or val1))
            except sqlite3.Error, e:
                return {"error":"sqlite3.Error: "+str(e)}
            return {"status":"attach succeeded"}

        if command == "commit":
            signal.alarm(10)
            self.m_sqlitedbconn.commit()
            signal.alarm(0)
            return {"status":"commit succeeded"}  # doesn't reach here if the signal fails




    def save_sqlite(self, scraperID, runID, short_name, unique_keys, data, swdatatblname):
        res = { }
        
        if type(data) == dict:
            data = [data]
        
        if not self.m_sqlitedbconn or swdatatblname not in self.sqlitesaveinfo:
            ssinfo = SqliteSaveInfo(self, scraperID, runID, short_name, swdatatblname)
            self.sqlitesaveinfo[swdatatblname] = ssinfo
            if not ssinfo.rebuildinfo() and data:
                ssinfo.buildinitialtable(data[0])
                ssinfo.rebuildinfo()
                res["tablecreated"] = swdatatblname
        else:
            ssinfo = self.sqlitesaveinfo[swdatatblname]
        
        
        nrecords = 0
        for ldata in data:
            newcols = ssinfo.newcolumns(ldata)
            if newcols:
                for i, kv in enumerate(newcols):
                    ssinfo.addnewcolumn(kv[0], kv[1])
                    res["newcolumn %d" % i] = "%s %s" % kv
                ssinfo.rebuildinfo()

            if nrecords == 0 and unique_keys:
                idxname, idxkeys = ssinfo.findclosestindex(unique_keys)
                if not idxname or idxkeys != set(unique_keys):
                    lres = ssinfo.makenewindex(idxname, unique_keys)
                    if "error" in lres:  
                        return lres
                    res.update(lres)
            
            lres = ssinfo.insertdata(ldata)
            if "error" in lres:  
                return lres
            nrecords += 1
        self.m_sqlitedbconn.commit()
        res["nrecords"] = nrecords
        res["status"] = 'Data record(s) inserted or replaced'
        return res


class SqliteSaveInfo:
    def __init__(self, database, scraperID, runID, short_name, swdatatblname):
        self.database = database
        self.scraperID = scraperID
        self.runID = runID
        self.short_name = short_name
        self.swdatatblname = swdatatblname
        self.swdatakeys = [ ]
        self.swdatatypes = [  ]
        self.sqdatatemplate = ""

    def sqliteexecute(self, val1, val2=None):
        res = self.database.sqlitecommand(self.scraperID, self.runID, self.short_name, "execute", val1, val2)
        #print "execute", val1, val2, res
        return res
    
    def rebuildinfo(self):
        if not self.sqliteexecute("select * from main.sqlite_master where name=?", (self.swdatatblname,))["data"]:
            return False

        tblinfo = self.sqliteexecute("PRAGMA main.table_info(`%s`)" % self.swdatatblname)
            # there's a bug:  PRAGMA main.table_info(swdata) returns the schema for otherdatabase.swdata 
            # following an attach otherdatabase where otherdatabase has a swdata and main does not
            
        self.swdatakeys = [ a[1]  for a in tblinfo["data"] ]
        self.swdatatypes = [ a[2]  for a in tblinfo["data"] ]
        self.sqdatatemplate = "insert or replace into main.`%s` values (%s)" % (self.swdatatblname, ",".join(["?"]*len(self.swdatakeys)))
        return True
            
    def buildinitialtable(self, data):
        assert not self.swdatakeys
        coldef = self.newcolumns(data)
        assert coldef
        # coldef = coldef[:1]  # just put one column in; the rest could be altered -- to prove it's good
        scoldef = ", ".join(["`%s` %s" % col  for col in coldef])
                # used to just add date_scraped in, but without it can't create an empty table
        self.sqliteexecute("create table main.`%s` (%s)" % (self.swdatatblname, scoldef))
    
    def newcolumns(self, data):
        newcols = [ ]
        for k in data:
            if k not in self.swdatakeys:
                v = data[k]
                if v != None:
                    if k[-5:] == "_blob":
                        vt = "blob"  # coerced into affinity none
                    elif type(v) == int:
                        vt = "integer"
                    elif type(v) == float:
                        vt = "real"
                    else:
                        vt = "text"
                    newcols.append((k, vt))
        return newcols

    def addnewcolumn(self, k, vt):
        self.sqliteexecute("alter table main.`%s` add column `%s` %s" % (self.swdatatblname, k, vt))

    def findclosestindex(self, unique_keys):
        idxlist = self.sqliteexecute("PRAGMA main.index_list(`%s`)" % self.swdatatblname)  # [seq,name,unique]
        uniqueindexes = [ ]
        for idxel in idxlist["data"]:
            if idxel[2]:
                idxname = idxel[1]
                idxinfo = self.sqliteexecute("PRAGMA main.index_info(`%s`)" % idxname) # [seqno,cid,name]
                idxset = set([ a[2]  for a in idxinfo["data"] ])
                idxoverlap = len(idxset.intersection(unique_keys))
                uniqueindexes.append((idxoverlap, idxname, idxset))
        
        if not uniqueindexes:
            return None, None
        uniqueindexes.sort()
        return uniqueindexes[-1][1], uniqueindexes[-1][2]

    # increment to next index number every time there is a change, and add the new index before dropping the old one.
    def makenewindex(self, idxname, unique_keys):
        istart = 0
        if idxname:
            mnum = re.search("(\d+)$", idxname)
            if mnum:
                istart = int(mnum.group(1))
        for i in range(10000):
            newidxname = "%s_index%d" % (self.swdatatblname, istart+i)
            if not self.sqliteexecute("select name from main.sqlite_master where name=?", (newidxname,))["data"]:
                break
            
        res = { "newindex": newidxname }
        lres = self.sqliteexecute("create unique index `%s` on `%s` (%s)" % (newidxname, self.swdatatblname, ",".join(["`%s`"%k  for k in unique_keys])))
        if "error" in lres:  return lres
        if idxname:
            lres = self.sqliteexecute("drop index main.`%s`" % idxname)
            if "error" in lres:  
                if lres["error"] != 'sqlite3.Error: index associated with UNIQUE or PRIMARY KEY constraint cannot be dropped':
                    return lres
                print "Dropping index", lres # to detect if it's happening repeatedly
            res["droppedindex"] = idxname
        return res
            
    def insertdata(self, data):
        values = [ data.get(k)  for k in self.swdatakeys ]
        return self.sqliteexecute(self.sqdatatemplate, values)

