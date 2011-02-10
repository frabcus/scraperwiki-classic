from scraperwiki.datastore import save_sqlite as save
from scraperwiki.datastore import sqlitecommand

def attach(name, asname=None):
    return sqlitecommand("attach", name, asname)
    
def execute(val1, val2=None):
    return sqlitecommand("execute", val1, val2)

def commit():
    return sqlitecommand("commit")



def select(val1, val2=None):
    result = sqlitecommand("execute", "select %s" % val1, val2)
    return [ dict(zip(result["keys"], d))  for d in result["data"] ]

def show_tables(dbname=""):
    name = "sqlite_master"
    if dbname:
        name = "%s.%s" % (dbname, name)
    result = sqlitecommand("execute", "select tbl_name, sql from %s where type='table'" % name)
    return dict(result["data"])

def table_info(name):
    sname = name.split(".")
    if len(sname) == 2:
        result = sqlitecommand("execute", "PRAGMA %s.table_info(`%s`)" % tuple(sname))
    else:
        result = sqlitecommand("execute", "PRAGMA table_info(`%s`)" % name)
    return [ dict(zip(result["keys"], d))  for d in result["data"] ]

def verbose(bverbose):
    sqlitecommand("verbose", bverbose)
