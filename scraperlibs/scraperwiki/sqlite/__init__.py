from scraperwiki.datastore import save_sqlite as save
from scraperwiki.datastore import sqlitecommand, SqliteError, NoSuchTableSqliteError


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



            # also needs to handle the types better (could save json and datetime objects handily
def save_var(name, value, commit=True, verbose=2):
    data = {"name":name, "value_blob":value, "type":type(value).__name__}
    save(unique_keys=["name"], data=data, table_name="swvariables", commit=commit, verbose=verbose)

def get_var(name, default=None, verbose=2):
    try:
        result = sqlitecommand("execute", "select value_blob, type from swvariables where name=?", (name,), verbose)
    except NoSuchTableSqliteError, e:
        return default
    data = result.get("data")
    if not data:
        return default
    return data[0][0]

    

    