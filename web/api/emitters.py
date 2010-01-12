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

def stringnot(v):
    if type(v) == float:
        return v
    elif type(v) == int:
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
            writer.writerow([stringnot(rowdict[key])  for key in allkeys])

        result = fout.getvalue()
        fout.close()
        return result
        

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
        response = StringIO.StringIO()

        content = self.construct()
        return_content = []
        for value in content:
            return_content.append(self.format_values(value))
        response.write(phpserialize.dumps(content))
        res =  response.getvalue()
        response.close
        return res
        

Emitter.register('csv', CSVEmitter, 'text/csv; charset=utf-8')
Emitter.register('php', PHPEmitter, 'text/plain; charset=utf-8')

