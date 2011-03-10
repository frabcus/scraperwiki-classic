from scraperwiki.datastore import save_sqlite as save
from scraperwiki.datastore import sqlitecommand


def attach(name, asname=None, verbose=1):
    return sqlitecommand("attach", name, asname, verbose)
    
def execute(val1, val2=None, verbose=1):
    if val2 is not None and "?" in val1 and type(val2) not in [list, tuple]:
        val2 = [val2]
    return sqlitecommand("execute", val1, val2, verbose)

def commit(verbose=1):
    return sqlitecommand("commit", None, None, verbose)



def select(val1, val2=None, verbose=1):
    if val2 is not None and "?" in val1 and type(val2) not in [list, tuple]:
        val2 = [val2]
    result = sqlitecommand("execute", "select %s" % val1, val2, verbose)
    return [ dict(zip(result["keys"], d))  for d in result["data"] ]

def show_tables(dbname=""):
    name = "sqlite_master"
    if dbname:
        name = "%s.%s" % (dbname, name)
    result = sqlitecommand("execute", "select tbl_name, sql from `%s` where type='table'" % name)
    return dict(result["data"])

def table_info(name):
    sname = name.split(".")
    if len(sname) == 2:
        result = sqlitecommand("execute", "PRAGMA %s.table_info(`%s`)" % tuple(sname))
    else:
        result = sqlitecommand("execute", "PRAGMA table_info(`%s`)" % name)
    return [ dict(zip(result["keys"], d))  for d in result["data"] ]

