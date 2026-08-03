from rest_framework import status


def api_response(message, data=None, errors=None, success=True, status_code=status.HTTP_200_OK):
    return {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "errors": errors if errors is not None else [],
    }, status_code
