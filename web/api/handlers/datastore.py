from api.handlers.api_base import APIBase

class Keys(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with format=jsonlist and limit 0" }

class Search(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"no search is possible across different databases" }

class DataByLocation(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite bounds on the lat lng values" }

class DataByDate(APIBase):
    def value(self, request):
        return { "error":"Sorry, this function has been deprecated.", "message":"use scraperwiki.datastore.sqlite with bounds on your date field" }

