from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from recuro import recurly_parser

@csrf_exempt
def notify(request):
    recurly_parser.parse(request.POST['body'])
    return HttpResponse("ok", mimetype="text/plain")
