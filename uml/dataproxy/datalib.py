import  ConfigParser
import  hashlib
import  types
import  os
import  string
import  time
import  types

dbtype  = 'mysql'
place   = '%s'
db      = None

def connection (config) :

    """
    Get a database connection. Creates one if it does not already exists,
    otherwise returns the extant one.
    """

    global dbtype
    global db
    global place

    if db is None :

        if type(config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(config))
        else :
            conf = config

        dbtype = conf.get ('dataproxy', 'dbtype')

        if dbtype == 'mysql'   :
            try    :
                import MySQLdb
                db      = MySQLdb.connect \
                        (    host       = conf.get ('dataproxy', 'host'  ), 
                             user       = conf.get ('dataproxy', 'user'  ), 
                             passwd     = conf.get ('dataproxy', 'passwd'),
                             db         = conf.get ('dataproxy', 'db'    ),
                             charset    = 'utf8'
                        )
                place   = '%s'
            except :
                raise Exception("Unable to connect to datastore")

        if dbtype == 'sqlite3' :
            try :
                from pysqlite2 import dbapi2 as sqlite
                db      = sqlite.connect (conf.get ('dataproxy', 'db'))
                place   = '?'
            except :
                raise Exception("Unable to connect to datastore")

        if db is None :
            raise Exception("Unrecognised datastore type '%s'" % dbtype)
        
    return db

def fixPlaceHolder (query) :

    """
    Fix place holders in query. Usually this is a null operation, but is needed
    for testing since the SQLite3 driver uses the (more sensible and standard)
    ? character as placeholder.
    """

    if place == '%s' :
        return query
    return query.replace ('%s', place)

def execute (query, values = None) :

    """
    Create a cursor and execute a query, returning the cursor as the result.
    """

    cursor = db.cursor()
    query  = fixPlaceHolder(query)
    if values is None :
           cursor.execute (query)
    else : cursor.execute (query, values)
    return cursor

def fixKVKey (key) :

    """
    Replace characters in a key such that it is a valid XML tag.
    (except that this can't work if there are other invalidities such as leading numbers -- 
    this mangling has been moved into datastore.save)
    """
    return key
    # was return key.replace (' ', '_')

def uniqueHash (unique, data) :

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

def nextItemID () :

    """
    Get a new item identifier value.
    """

    #  This is separated out since the code is a bit different for
    #  testing with SQLite3
    #
    if dbtype == 'mysql'   :
        cursor = execute ('UPDATE `sequences` SET `id` = LAST_INSERT_ID(`id`+1)')
        return cursor.lastrowid
    if dbtype == 'sqlite3' :
        cursor = execute ('UPDATE `sequences` SET `id` = `id` + 1')
        return execute('SELECT `id` FROM `sequences`').fetchone()[0]
    raise Exception("Unrecognised datastore type '%s'" % dbtype)

def fetch (scraperID, unique_keys) :

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
    cursor1 = execute \
        (   'SELECT `item_id`, `date`, `latlng`, `date_scraped` FROM items WHERE scraper_id = %s AND unique_hash = %s',
            [ scraperID, uhash ]
        )

    res     = []
    for row in cursor1.fetchall() :
        data   = {}
        cursor2 = execute ('SELECT `key`, `value` FROM `kv` where `item_id` = %s', [ row[0] ])
        for pair in cursor2.fetchall() :
            data[pair[0]] = pair[1]
        res.append ({ 'date' : str(row[1]), 'latlng' : row[2], 'date_scraped' : str(row[3]), 'data' : data })

    return [ True, res ]

def save (scraperID, unique_keys, scraped_data, date = None, latlng = None) :

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

    #  Map the scraped data to data to be stored. None, True and False are
    #  mapped to the empty string, one and zero respectively; anything else
    #  is turned into a string. The value is stored against a fixed key
    #  value.
    #
    insert_data = {}
    for key, value in scraped_data.items() :
        if   value is None          : value = ""
        elif value is True          : value = "1"
        elif value is False         : value = "0"
        elif type(value) != types.UnicodeType   : value = str(value)
        insert_data[fixKVKey(key)] = value

    #   This is the Julian/Francis code. Reverted back to Sym's because this
    #   is horribly expensive.
    #
    #   query  = []
    #   values = []
    #   slot   = 1
    #   query.append ('SELECT items.item_id AS item_id FROM items')
    #   for key in unique :
    #       query .append ('INNER JOIN kv kv%03d ON kv%03d.item_id = items.item_id AND kv%03d.key = %%s' % (slot, slot, slot))
    #       values.append (key)
    #       if data.has_key(key) :
    #           if data[key] is not None :
    #                  query .append ('AND kv%03d.value = %%s'   % (slot))
    #                  values.append (data[key])
    #           else : query .append ('AND kv%30d.value is null' % (slot))
    #   query .append ('WHERE items.scraper_id = %s')
    #   values.append (scraperID)
    #   cursor = execute (string.join (query,  ' '), values)
    #   idlist = [ str(row[0]) for row in cursor.fetchall() ]

    if scraperID in [ None, '' ] :
        return  [ True, 'Data OK to save' ]

    #  Look for existing values via the unique hash on the values of the unique
    #  keys.
    #
    uhash = uniqueHash (unique_keys, scraped_data)
    cursor = execute ('SELECT item_id FROM items WHERE scraper_id = %s AND unique_hash = %s', (scraperID, uhash))
    idlist = [ str(row[0]) for row in cursor.fetchall() ]

    #  Special case if more than one item was matched, which should actually
    #  never occur. If it does then just delete all key/value pairs and all
    #  items.
    #
    if len(idlist) >  1 :

        execute ('DELETE FROM `kv`    WHERE `item_id` IN (%s)' % string.join(idlist, ','))
        execute ('DELETE FROM `items` WHERE `item_id` in (%s)' % string.join(idlist, ','))

    #  If exactly one record matched then see if the other values have changed;
    #  if not then do nothing with the data and return "already exists", else
    #  update the values and return "updated". In either casse, update the lat/lng
    #  and date in the items record.
    #
    if len(idlist) == 1 :

        execute ('UPDATE `items` SET `date` = %s, `latlng` = %s WHERE `item_id` = %s', ( date, latlng, idlist[0] ))

        extant_data = {}
        cursor = execute ('SELECT `key`, `value` from `kv` WHERE `item_id` = %s', ( idlist[0], ))
        for key, value in cursor.fetchall() :
            extant_data[key] = value
        if extant_data == insert_data :
            return [ True, 'Data record already exists' ]

        for key, value in insert_data.items() :
            execute \
                (   '''
                    UPDATE  `kv`
                    SET     `value`     = %s
                    WHERE   `item_id`   = %s
                    AND     `key`       = %s
                    ''',
                    [   value, idlist[0], key   ]
                )
        return  [ True, 'Data record updated' ]

    #  New data to be inserted. Get a new item identifier and then insert
    #  the items record and the key-valuye pairs.
    #
    itemid = nextItemID ()

    execute \
        (       '''
                INSERT  INTO    `items`
                        (       `item_id`,
                                `unique_hash`,
                                `scraper_id`,
                                `date`,
                                `latlng`,
                                `date_scraped`
                                )
                VALUES  (        %s, %s, %s, %s, %s, %s
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
        execute \
            (       '''
                    INSERT INTO    `kv`
                            (       `item_id`,
                                    `key`,
                                    `value`
                            )
                    VALUES  (        %s, %s, %s
                            )
                    ''',
                    (       itemid,
                            key,
                            value
                    )
            )

    return  [ True, 'Data record inserted' ]
