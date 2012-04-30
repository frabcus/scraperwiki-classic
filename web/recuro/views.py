from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from recuro import recurly_parser

@csrf_exempt
def notify(request, apikey):
    if apikey != settings.RECURLY_API_KEY:
        return HttpResponseForbidden()
    obj = recurly_parser.parse(request.raw_post_data)
    obj.save()
    return HttpResponse("ok", mimetype="text/plain")
