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

class CSVEmitter(Emitter):
    """
    Emitter for exporting to CSV (excel dialect).
    """
    def get_keys(self, input_dict):
        keys = []
        for item in input_dict.items():
            if isinstance(item[1], dict):
                keys.extend(self.get_keys(item[1]))
            else:
                keys.append(item[0])
        return keys
    
    def get_values(self, input_dict):
        for item in input_dict.items():
            if isinstance(item[1], dict):
                input_dict.update(self.get_values(input_dict.pop(item[0])))
            elif isinstance(item[1], list):
                input_dict[item[0]] = smart_str(" ".join(i for i in item[1]))
            else:
                input_dict[item[0]] = smart_str(item[1])
        return input_dict
    
    def render(self, request):
        response = StringIO.StringIO()
        content = self.construct()
        keys = self.get_keys(content[0])

        writer = csv.DictWriter(response, keys, dialect='excel')
        headers = dict((n,n) for n in keys)
        writer.writerow(headers)
        for row in content:
            writer.writerow(self.get_values(row))

        res =  response.getvalue()
        response.close
        return res
        
Emitter.register('csv', CSVEmitter, 'text/csv; charset=utf-8')



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
        
Emitter.register('php', PHPEmitter, 'text/plain; charset=utf-8')