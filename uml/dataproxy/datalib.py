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

    def __init__(self, ldataproxy, config, scraperID):
        self.dataproxy = ldataproxy

        self.m_sqlitedbconn = None
        self.m_sqlitedbcursor = None
        self.authorizer_func = None  
        
        self.sqlitesaveinfo = { }  # tablename -> info

        if type(config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(config))
        else :
            conf = config

        self.m_resourcedir = conf.get('dataproxy', 'resourcedir')


    def clear_datastore(self, scraperID, short_name):
        scraperresourcedir = os.path.join(self.m_resourcedir, short_name)
        scrapersqlitefile = os.path.join(scraperresourcedir, "defaultdb.sqlite")
        if os.path.isfile(scrapersqlitefile):
            deletedscrapersqlitefile = os.path.join(scraperresourcedir, "DELETED-defaultdb.sqlite")
            shutil.move(scrapersqlitefile, deletedscrapersqlitefile)
        return {"status":"good"}

    # general single file sqlite access
    # the values of these fields are safe because from the UML they are subject to an ident callback, 
    # and from the frontend they are subject to a connection from a particular IP number
    def sqlitecommand(self, scraperID, runID, short_name, command, val1, val2):
        print "XXXXX", (command, runID, val1, val2, self.m_sqlitedbcursor, self.m_sqlitedbconn)
        
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
            
            result = { "filename":lscrapersqlitefile, "filesize": os.path.getsize(scrapersqlitefile)}
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
                        return {"status":"No sqlite database"}    # don't make one if we're just requesting a summary
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
                
                    # this loop has the one internal jsend in it
                while True:
                    data = self.m_sqlitedbcursor.fetchmany(val2[1])
                    arg = {"keys":keys, "data":data} 
                    if len(data) < val2[1]:
                        break
                    arg["moredata"] = True
                    self.dataproxy.connection.send(json.dumps(arg)+'\n')
                return arg

            
            except sqlite3.Error, e:
                signal.alarm (0)
                return {"error":"sqlite3.Error: "+str(e)}
                
        elif command == "datasummary":
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
        
        elif command == "attach":
            if self.authorizer_func == authorizer_writemain:
                self.m_sqlitedbconn.commit()  # otherwise a commit will be invoked by the attaching function
            self.authorizer_func = authorizer_attaching
            try:
                attachscrapersqlitefile = os.path.join(self.m_resourcedir, val1, "defaultdb.sqlite")
                self.m_sqlitedbcursor.execute('attach database ? as ?', (attachscrapersqlitefile, val2 or val1))
            except sqlite3.Error, e:
                return {"error":"sqlite3.Error: "+str(e)}
            return {"status":"attach succeeded"}

        elif command == "commit":
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
        #print ["execute", val1, val2, res]
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

