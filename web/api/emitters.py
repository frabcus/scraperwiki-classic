import datetime
import time
import csv
from django.utils.encoding import smart_str

from piston.emitters import Emitter
import phpserialize

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


class CSVEmitter(Emitter):
    """
    Emitter for exporting to CSV (excel dialect).
    """
    
    # code here itentical to scraperwiki/web/scraper/views.py export_csv()
    def render(self, request):
        dictlist = self.construct()
        
        keyset = set()
        for row in dictlist:
            if "latlng" in row:   # split the latlng
                row["lat"], row["lng"] = row.pop("latlng") 
            row.pop("date_scraped") 
            keyset.update(row.keys())
        allkeys = sorted(keyset)
        
        fout = StringIO.StringIO()
        writer = csv.writer(fout, dialect='excel')
        writer.writerow(allkeys)
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
        for item in value.items():
            if isinstance(item[1], datetime.datetime):
                value[item[0]] = time.mktime(item[1].timetuple())
        return value
        
    def render(self, request):

        dictlist = self.construct()
        return_content = []
        for rowdict in dictlist:
            for key in rowdict.keys():
                # convert datetime to Epoch time
                if isinstance(rowdict[key], datetime.datetime):
                    rowdict[key] = time.mktime(rowdict[key].timetuple())
            return_content.append(rowdict)
        
        result = phpserialize.dumps(return_content)
        return result
