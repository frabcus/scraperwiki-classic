# Taken wholesale from https://github.com/scdoshi/django-cors/blob/master/cors.py

from django.conf import settings

#: By default we'll set CORS Allow Origin * for all application/json responses
DEFAULT_CORS_PATHS = (
	('/', ('application/json', ),('*',), ),
)

class CORSMiddleware(object):
	"""
	From https://github.com/acdha/django-sugar/blob/master/sugar/middleware/cors.py

	Middleware that serves up representations with a CORS header to
	allow third parties to use your web api from JavaScript without
	requiring them to proxy it.

	See: http://www.w3.org/TR/cors/

	Installation
	------------

	1. Add to ``settings.MIDDLEWARE_CLASSES``::

	'sugar.middleware.cors.CORSMiddleware',

	2. Optionally, configure ``settings.CORS_PATHS`` if the default settings
	aren't appropriate for your application. ``CORS_PATHS`` should be a
	list of (path, content_types, headers) values where content_types and
	headers are lists of mime types and (key, value) pairs, respectively.

	Processing occurs first to last so you should order ``CORS_PATHS``
	items from most to least specific.

	See ``DEFAULT_CORS_PATHS`` for an example.
	"""

	def __init__(self):
		self.paths = getattr(settings, "CORS_PATHS", DEFAULT_CORS_PATHS)

	def process_response(self, request, response):
		content_type = response.get('content-type', '').split(";")[0].lower()

		for path, types, allowed in self.paths:
			if request.path.startswith(path) and content_type in types:

				for domain in allowed:
					response['Access-Control-Allow-Origin'] = domain
					response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
					response['Access-Control-Max-Age'] = 1000
					response['Access-Control-Allow-Headers'] = '*'
				break
		return response