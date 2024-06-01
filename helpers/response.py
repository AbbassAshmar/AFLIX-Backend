
def successResponse(data, metadata) : 
    return {
        "status" : "success",
        "error" : None,
        "data" : data,
        "metadata" : metadata
    }

def failedResponse(error, metadata) : 
    return {
        "status" : "failed",
        "error" : error,
        "data" : None,
        "metadata" : metadata
    }
