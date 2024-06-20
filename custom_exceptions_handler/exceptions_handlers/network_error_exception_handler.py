from rest_framework.views import exception_handler
from helpers.response import failedResponse
from rest_framework.response import Response
from custom_exceptions.custom_exceptions import NetworkError


def network_error_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, NetworkError) and response is not None:
        detail_message = str(exc.detail) if exc.detail else "Network Error."
        error = {'message' : detail_message,'code' : 500}
        response = Response(failedResponse(error,None), 500)

    return response