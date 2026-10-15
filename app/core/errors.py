import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

STATUS_CODES = {
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
}


class AppError(Exception):
    """Raised by services. Handlers turn it into the standard error body."""

    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def error_body(request: Request, code: str, message: str, details=None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": request.headers.get("x-request-id") or str(uuid.uuid4()),
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(request, exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            parts = [str(p) for p in err["loc"] if p not in ("body", "query", "path")]
            issue = err["msg"].removeprefix("Value error, ")
            details.append({"field": ".".join(parts), "issue": issue})
        return JSONResponse(
            status_code=422,
            content=error_body(request, "VALIDATION_ERROR", "Validation failed", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        code = STATUS_CODES.get(exc.status_code, "ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(request, code, str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        # never show a stack trace to the caller
        return JSONResponse(
            status_code=500,
            content=error_body(request, "INTERNAL_ERROR", "Internal server error"),
        )