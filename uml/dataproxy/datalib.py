import  ConfigParser
import  hashlib
import  types
import  os
import  string
import  time
import  types
import  datetime

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

    def connect (self, config, scraperID) :

        """
        Get a database connection.
        """

        self.m_db = None

        if type(config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(config))
        else :
            conf = config

        self.m_dbtype = conf.get ('dataproxy', 'dbtype')

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
                raise Exception("Unable to connect to datastore: %s" % e)

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
                raise Exception("Unable to connect to datastore: %s" % e)

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

        cursor = self.m_db.cursor()
        query  = self.fixPlaceHolder(query)
        if values is None :
               cursor.execute (query)
        else : cursor.execute (query, values)
        return cursor

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

    def fetch (self, scraperID, unique_keys) :   # note: unique_keys is a dict in the function, whereas elsewhere it is a list!

        """
        Fetch values from the datastore.
        """

        #  Sanity checks
        #
        if type(unique_keys) not in [ types.DictType ] or len(unique_keys) == 0 :
            return [ False, 'unique_keys must be a non-empty dictionary' ]

        if scraperID in [ None, '' ] :
            return [ False, 'cannot fetch data without a scraper ID' ]

        uhash   = uniqueHash (unique_keys.keys(), unique_keys)
        cursor1 = self.execute \
                    (   'select `item_id`, `date`, `latlng`, `date_scraped` from `items` where `scraper_id` = %s and `unique_hash` = %s',
                        [ scraperID, uhash ]
                    )

        res     = []
        for row in cursor1.fetchall() :
            data   = {}
            cursor2 = self.execute ('select `key`, `value` from `kv` where `item_id` = %s', [ row[0] ])
            for pair in cursor2.fetchall() :
                data[pair[0]] = pair[1]
            res.append ({ 'date' : str(row[1]), 'latlng' : row[2], 'date_scraped' : str(row[3]), 'data' : data })

        return [ True, res ]


    def postcodeToLatLng (self, scraperID, postcode) :   

        postcode = postcode.upper().replace(' ', '')
        cursor   = self.execute ('select x(location), y(location) from `postcode_lookup` where `postcode` = %s', [ postcode ])
        try :
            result = cursor.fetchone()
            return [ True,  ( result[0], result[1] ) ]
        except :
            return [ False, 'Postcode not found' ]

    def retrieve (self, scraperID, matchrecord) :   

        """
        Retrieve matched values ignoring hashcode technology
        """

        query  = []
        values = []
        slot   = 1
        query.append('select `items`.`item_id`, `date`, `latlng`, `date_scraped` from `items`')
        for key, value in matchrecord.items():
            query .append(' inner join `kv` as kv%03d on kv%03d.`item_id` = `items`.`item_id` and kv%03d.`key` = %%s' % (slot, slot, slot))
            values.append(key)
            if value != "":
            #if value is not None:  # can't transfer None through at the moment
                query.append(' and kv%03d.`value` = %%s' % (slot))
                values.append(value)
            slot += 1
        query.append(' where `items`.`scraper_id` = %s')
        values.append(scraperID)
    
        cursor1 = self.execute("".join(query), values)
    
        # same code as in retrieve
        res     = []
        for row in cursor1.fetchall() :
            data   = {}
            cursor2 = self.execute ('select `key`, `value` from `kv` where `item_id` = %s', [ row[0] ])
            for pair in cursor2.fetchall() :
                data[pair[0]] = pair[1]
            res.append ({ 'date' : str(row[1]), 'latlng' : row[2], 'date_scraped' : str(row[3]), 'data' : data })

        return [ True, res ]


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

            self.execute ('delete from `kv`    where `item_id` in (%s)' % string.join(idlist, ','))
            self.execute ('delete from `items` where `item_id` in (%s)' % string.join(idlist, ','))

        #  If exactly one record matched then see if the other values have changed;
        #  if not then do nothing with the data and return "already exists", else
        #  update the values and return "updated". In either casse, update the lat/lng
        #  and date in the items record.
        #
        if len(idlist) == 1 :

            import sys
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

            self.m_db.commit()
            return  [ True, 'Data record updated' ]

        #  New data to be inserted. Get a new item identifier and then insert
        #  the items record and the key-valuye pairs.
        #
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
    
        self.m_db.commit()
    
        return  [ True, 'Data record inserted' ]


    def data_dictlist (self, scraperID, limit, offset, start_date, end_date, latlng) :

        qquery  = [ "select `items`.`item_id` as `item_id`" ]
        qparams = []

        if latlng is not None :
            qquery .append(", substr(`items`.`latlng`,  1, 20)")
            qquery .append(", substr(`items`.`latlng`, 21, 41)")
            qquery .append(", abs(substr(`items`.`latlng`, 1, 20) - %s) + abs(substr(`items`.`latlng`, 21, 41) - %s) as diamdist")
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
            qparams.append(settings.MAX_API_DISTANCE_KM)            
            qquery .append("order by distance asc")
        else :
            qquery .append("order by `date_scraped` desc")

#       qquery .append("limit %s,%s")
#       qparams.append(offset)
#       qparams.append(limit)

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
                rdata["latlng"] = tuple(map(float, item[1].split(",")))
        
            allitems.append (rdata)

        return [ True, allitems ]

    def clear_datastore (self, scraperID) :
                # this line is very slow due to sub-tables.  
                # could it be done with self.execute ("delete from `kv` where inner join `items` on `kv`.`item_id` = `items`.`item_id` where `items`.`scraper_id` = %s)", (scraperID,))
        self.execute ("delete from `kv` where `item_id` in (select `item_id` from `items` where `scraper_id` = %s)", (scraperID,))
        self.execute ("delete from `items` where `scraper_id` = %s", (scraperID,))
        self.m_db.commit()
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

    def item_count (self, scraperID) :

        cursor = self.execute ("select count(`item_id`) from `items` where `scraper_id` = %s", (scraperID, ))
        return [ True, int(cursor.fetchone()[0]) ]

    def has_geo (self, scraperID) :

        cursor = self.execute ("select count(`item_id`) from `items` where `scraper_id` = %s and latlng is not null and latlng != ''", (scraperID,))
        return [ True, int(cursor.fetchone()[0]) > 0 ]

    def has_temporal (self, scraperID) :

        cursor = self.execute ("select count(`item_id`) from `items` where `scraper_id` = %s and date is not null", (scraperID,))
        return [ True, int(cursor.fetchone()[0]) > 9 ]

    def recent_record_count (self, scraperID, days) :

        sql = '''
              select date(`date_scraped`) as date, count(`date_scraped`) as count from `items`
                     where `scraper_id` = %s and `date_scraped` between date_sub(curdate(), interval %s day) and date_add(curdate(), interval 1 day)
                     group by date(`date_scraped`)
              '''
        cursor = self.execute (sql, (scraperID, days))
        date_counts = cursor.fetchall()

        #make a store, 
        return_dates = []
        all_dates    = [datetime.datetime.now() + datetime.timedelta(i)  for i in range(-days, 1)]
        for all_date in  all_dates:
            #try and find an entry for this date in the query results
            count = 0
            for date_count in date_counts :
                if str(date_count[0]) == all_date.strftime("%Y-%m-%d") :
                    count = date_count[1]

            #add the count to the return list
            return_dates.append(count)
        
        return [ True, return_dates ]
