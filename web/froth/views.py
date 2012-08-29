import json
from django.http import HttpResponse
from frontend.models import UserProfile


def check_key(request, apikey):
    p = UserProfile.objects.filter(apikey=apikey)
    print apikey, len(p)
    if len(p) == 0:
        status = 403 # Forbidden
        content = {'error':'Forbidden'}
    elif p[0].user.is_staff:
        status = 200 # Okay
    elif p[0].plan == 'free':
        status = 402 # Pay
        content = {'error':'Pay'}
    else:
        status = 200 # Okay
    if status == 200:
        content = {'org':p[0].user.username}
    return HttpResponse(json.dumps(content), mimetype="text/plain", status=status)
