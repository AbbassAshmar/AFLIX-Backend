from rest_framework.views import exception_handler
from helpers.response import failedResponse
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


def validation_error_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError) and response is not None:
        metadata = {'error_fields' : []}
        error = {
            'code' : 400,
            'message' : "Validation error.",
            "details" : {}
        }

        if exc.detail : 
            for key in exc.detail : 
                if key == "message" : 
                    error["message"] =  exc.detail[key]
                    continue

                if exc.detail[key] :
                    error['details'][key] = exc.detail[key]
                    
                metadata['error_fields'].append(key)

        payload = failedResponse(error, metadata)
        response = Response(payload, 400)

    return response