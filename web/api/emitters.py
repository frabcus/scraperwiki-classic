import datetime
import time
import csv
from django.utils.encoding import smart_str
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.utils import simplejson
from piston.emitters import Emitter
import phpserialize
import gviz_api

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

# The Emitter.construct() function returns a value from scraperwiki/web/scraper/managers/scraper.py data_dictlist() 

def stringnot(v):
    if v == None:
        return ""
    if type(v) == float:
        return v
    if type(v) == int:
        return v
    return smart_str(v)


# this code has departed from the documentation that says construct() must return a dict
# http://bitbucket.org/jespern/django-piston/wiki/Documentation#emitters
# so we're going to deal with the forms that come through as it's easier than repairing this error properly
# (The default JSONEmitter is tolerant of this error as it merely does a json dumps on the value)
class CSVEmitter(Emitter):
    """
    Emitter for exporting to CSV (excel dialect).
    """
    
    def render(self, request):
        dictlist = self.construct()
        return self.to_csv(dictlist)

    @staticmethod
    def to_csv(dictlist, headings=True):
        
        fout = StringIO.StringIO()
        writer = csv.writer(fout, dialect='excel')
        
        # identify and deal with the case of getKeys which is a list of strings
        if dictlist and type(dictlist[0]) != dict:
            writer.writerow([k.encode('utf-8') for k in dictlist])
            return fout.getvalue()
        
        # identify the sqlite keys and data case
        if "error" in dictlist[0]:
            return str(dictlist[0]["error"])
        if "keys" in dictlist[0] and "data" in dictlist[0]:
            if headings:
                writer.writerow([k.encode('utf-8') for k in dictlist[0]["keys"]])
            for row in dictlist[0]["data"]:
                writer.writerow([ stringnot(v)  for v in row ])
            result = fout.getvalue()
            fout.close()
            return result
        
        keyset = set()
        for row in dictlist:
            if "latlng" in row and len("latlng") == 2:   # split the latlng
                try:
                    row["latlng_lat"], row["latlng_lng"] = row.pop("latlng") 
                except:
                    pass
            row.pop("date_scraped", None) 
            keyset.update(row.keys())
        allkeys = sorted(keyset)
        
        if headings:
            writer.writerow([k.encode('utf-8') for k in allkeys])
        for rowdict in dictlist:
            writer.writerow([stringnot(rowdict.get(key))  for key in allkeys])

        result = fout.getvalue()
        fout.close()
        return result


def phpstringnot(v):
    if isinstance(v, datetime.datetime):
        return time.mktime(v.timetuple())
    return v

class PHPEmitter(Emitter):
    """
    Emitter for exporting to phpserialize's strings 
    """
    
    def format_values(self, value):
        if isinstance(value, dict):
            keys = value.keys()
        elif isinstance(value, list):
            keys = range(len(value))
        else:
            return
        
        for k in keys:
            v = value[k]
            tv = type(v)
            if tv == datetime.datetime:
                value[k] = time.mktime(v.timetuple())
            elif tv == list or tv == dict:
                self.format_values(v)  # recursive
                
        
    def render(self, request):
        dictlist = self.construct()
        self.format_values(dictlist)
        return phpserialize.dumps(dictlist)


class GVizEmitter(Emitter):
    def render(self, request):
        dictlist = self.construct()

        keyset = set()
        for row in dictlist:
            if "latlng" in row:   # split the latlng
                row["lat"], row["lng"] = row.pop("latlng")
            row.pop("date_scraped", None)
            keyset.update(row.keys())
        allkeys = sorted(keyset)

        description = {}
        for key in allkeys:
            description[key] = ('string', key)

        data_table = gviz_api.DataTable(description)
        data_table.LoadData(dictlist)

        return unicode(data_table.ToJSonResponse())

class JSONDICTEmitter(Emitter):
    """
    copied from base code
    """
    def render(self, request):
        cb = request.GET.get('callback')
        dictlist = self.construct()
        if "keys" in dictlist[0] and "data" in dictlist[0]:
            dictlist[0] = [ dict(zip(dictlist[0]["keys"], values))  for values in dictlist[0]["data"] ]
        seria = simplejson.dumps(dictlist, cls=DateTimeAwareJSONEncoder, indent=4)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria
