from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound
from .exceptions_handlers.not_found_exception_handler import not_found_exception_handler

def custom_exceptions_handler(exc, context):

    if isinstance(exc, NotFound):
        return not_found_exception_handler(exc, context)

    return exception_handler(exc, context)

