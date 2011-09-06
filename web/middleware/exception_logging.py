from django.utils.log import getLogger
import sys

logger = getLogger('django.request')

class ExceptionLoggingMiddleware(object):
    def process_exception(self, request, exception):
        import traceback
        logger.error('ExceptionLoggingMiddleware caught: ' + str(exception), exc_info=sys.exc_info())
        return None


