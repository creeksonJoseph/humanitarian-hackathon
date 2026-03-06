from typing import Any, Dict, Optional
from werkzeug.exceptions import HTTPException


class ApplicationError(Exception):
    """Generic application error with HTTP status and machine code.

    Use this to raise controlled errors from your code. Example:
        raise ApplicationError(status_code=409, code="job_already_claimed", message="Job already claimed")
    """

    def __init__(self, *, status_code: int = 400, code: str = "error", message: str = "An error occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def format_error(code: str, message: str, status: int = 400, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    payload["status"] = status
    return payload


def http_exception_to_dict(exc: HTTPException) -> Dict[str, Any]:
    return format_error(code=getattr(exc, 'name', 'http_error').lower().replace(' ', '_'), message=exc.description or exc.name, status=exc.code or 500)
