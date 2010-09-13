from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag
from django.db import IntegrityError
from django.contrib.auth.models import User

from django.conf import settings

from codewiki import models
import vc
import frontend
import urllib

import subprocess
import re

try:                import json
except ImportError: import simplejson as json


def rpcexecute_dummy(request, scraper_short_name, revision = None):
    response = HttpResponse()
    response.write('''
    <html>
      <head>
        <script type='text/javascript' src='http://www.google.com/jsapi'></script>
        <script type='text/javascript'>
          google.load('visualization', '1', {'packages':['annotatedtimeline']});
          google.setOnLoadCallback(drawChart);
          function drawChart() {
            var data = new google.visualization.DataTable();
            data.addColumn('date', 'Date');
            data.addColumn('number', 'Sold Pencils');
            data.addColumn('string', 'title1');
            data.addColumn('string', 'text1');
            data.addColumn('number', 'Sold Pens');
            data.addColumn('string', 'title2');
            data.addColumn('string', 'text2');
            data.addRows([
              [new Date(2008, 1 ,1), 30000, undefined, undefined, 40645, undefined, undefined],
              [new Date(2008, 1 ,2), 14045, undefined, undefined, 20374, undefined, undefined],
              [new Date(2008, 1 ,3), 55022, undefined, undefined, 50766, undefined, undefined],
              [new Date(2008, 1 ,4), 75284, undefined, undefined, 14334, 'Out of Stock','Ran out of stock on pens at 4pm'],
              [new Date(2008, 1 ,5), 41476, 'Bought Pens','Bought 200k pens', 66467, undefined, undefined],
              [new Date(2008, 1 ,6), 33322, undefined, undefined, 39463, undefined, undefined]
            ]);

            var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('chart_div'));
            chart.draw(data, {displayAnnotations: true});
          }
        </script>
      </head>

      <body style="height:10000px;">
        <div id='chart_div' style='width: 700px; height: 240px;'></div>

      </body>
    </html>
    '''
    )
    return response
                        
                        
# quick hack the manage the RPC execute feature 
# to test this locally you need to use python manage.py runserver twice, on 8000 and on 8010, 
# and view the webpage on 8010
def rpcexecute(request, scraper_short_name, revision = None):
    
    #if settings.USE_DUMMY_VIEWS == True:
    #    return rpcexecute_dummy(request, scraper_short_name, revision)
    
    scraper = get_object_or_404(models.View.objects, short_name=scraper_short_name)
    runner_path = "%s/runner.py" % settings.FIREBOX_PATH
    failed = False

    
    urlquerystring = request.META["QUERY_STRING"]
    # derive the function and arguments from the urlargs
    # (soon to be deprecated)
    rargs = { }
    for key in request.GET.keys():
        rargs[str(key)] = request.GET.get(key)
    func = rargs.pop("function", None)
    for key in rargs.keys():
        try: 
            rargs[key] = json.loads(rargs[key])
        except:
            pass
    
    args = [runner_path]
    args.append('--guid=%s' % scraper.guid)
    args.append('--language=%s' % scraper.language.lower())
    args.append('--name=%s' % scraper.short_name)
    args.append('--cpulimit=80')
    args.append('--urlquery=%s' % urlquerystring)
    
    runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    runner.stdin.write(scraper.saved_code(revision))
    
    # append in the single line at the bottom that gets the rpc executed with the right function and arguments
    #if func:
    #    runner.stdin.write("\n\n%s(**%s)\n" % (func, repr(rargs)))

    runner.stdin.close()

    response = HttpResponse()
    for line in runner.stdout:
        try:
            message = json.loads(line)
            print "mmmm", message
            if message['message_type'] == 'fail':
                failed = True
            elif message['message_type'] == 'exception':
                response.write("<h3>%s</h3>\n" % str(message["jtraceback"].get("exceptiondescription")).replace("<", "&lt;"))
                for stackentry in message["jtraceback"]["stackdump"]:
                    response.write("<h3>%s</h3>\n" % re.replace("<", "&lt;", str(stackentry).replace("<", "&lt;")))

            # recover the message from all the escaping
            if message['message_type'] == "console" and message.get('message_sub_type') != 'consolestatus':
                response.write(message["content"])

        except:
            pass
        
    return response
