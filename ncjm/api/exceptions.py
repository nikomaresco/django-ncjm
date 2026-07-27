from rest_framework import status
from rest_framework.exceptions import APIException, ErrorDetail, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


def _status_default_message(status_code):
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "Bad request."
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication required."
    if status_code == status.HTTP_403_FORBIDDEN:
        return "Permission denied."
    if status_code == status.HTTP_404_NOT_FOUND:
        return "Resource not found."
    if status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return "Method not allowed."
    if status_code == status.HTTP_409_CONFLICT:
        return "Conflict."
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "Too many requests."
    return "Request failed."


def _extract_message(data, status_code):
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, ErrorDetail):
            return str(detail)
        if isinstance(detail, str):
            return detail

    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, ErrorDetail):
            return str(first)
        if isinstance(first, str):
            return first

    return _status_default_message(status_code)


def _extract_code(exc, data):
    if isinstance(exc, ValidationError):
        return "validation_error"

    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, ErrorDetail):
            return detail.code

    code = getattr(exc, "default_code", None)
    if code:
        return str(code)

    return "error"


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    message = _extract_message(response.data, response.status_code)
    code = _extract_code(exc, response.data)

    response.data = {
        "error": {
            "status": response.status_code,
            "code": code,
            "message": message,
            "details": response.data,
        }
    }

    return response
