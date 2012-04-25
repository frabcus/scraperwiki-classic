from recuro import recurly_parser

def notify(request):
    recurly_parser.parse(request.POST['body'])
