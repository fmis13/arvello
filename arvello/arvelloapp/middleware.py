from threading import local
from django.utils.deprecation import MiddlewareMixin

_thread_locals = local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class RequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.request = request
        return None

    def process_response(self, request, response):
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response
