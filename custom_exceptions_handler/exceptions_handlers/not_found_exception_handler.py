from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound
from helpers.response import failedResponse
from rest_framework.response import Response

def not_found_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # NotFound handler
    if isinstance(exc, NotFound) and response is not None:
        detail_message = str(exc.detail) if exc.detail else "Resource not found."
        error = {'message' : detail_message,'code' : 404}
        response = Response(failedResponse(error,None), 404)

    return response