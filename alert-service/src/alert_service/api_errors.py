import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from alert_service.contracts import ErrorResponse

logger = logging.getLogger(__name__)


class RepositoryError(RuntimeError):
    """Raised when the persistence layer fails."""


try:
    _HTTP_422 = status.HTTP_422_UNPROCESSABLE_CONTENT
except AttributeError:
    _HTTP_422 = status.HTTP_422_UNPROCESSABLE_ENTITY


_STATUS_TO_ERROR_CODE = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    _HTTP_422: "VALIDATION_ERROR",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}


def build_error_response(
    status_code: int,
    message: str,
    details: Any | None = None,
    error_code: str | None = None,
) -> ErrorResponse:
    return ErrorResponse(
        success=False,
        error_code=error_code or _STATUS_TO_ERROR_CODE.get(status_code, "ERROR"),
        message=message,
        details=details,
    )


def _json_error_response(
    status_code: int,
    message: str,
    details: Any | None = None,
    error_code: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=build_error_response(
            status_code=status_code,
            message=message,
            details=details,
            error_code=error_code,
        ).model_dump(),
    )


def _http_exception_payload(exc: StarletteHTTPException) -> tuple[str, Any | None]:
    if isinstance(exc.detail, dict):
        return exc.detail.get("message", "HTTP error"), exc.detail
    if isinstance(exc.detail, list):
        return "HTTP error", exc.detail
    return str(exc.detail), None


class ErrorStandardizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that standardizes error responses for 404 and 405 errors.
    This is needed because these errors are generated before exception handlers run.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            logger.debug("404 Not Found: %s %s", request.method, request.url.path)
            return _json_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Route not found: {request.method} {request.url.path}",
                error_code="NOT_FOUND",
            )

        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            logger.debug("405 Method Not Allowed: %s %s", request.method, request.url.path)
            return _json_error_response(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                message=f"Method not allowed: {request.method} {request.url.path}",
                error_code="METHOD_NOT_ALLOWED",
            )

        return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for standardized error responses"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle FastAPI/Starlette HTTPException"""
        message, details = _http_exception_payload(exc)
        return _json_error_response(
            status_code=exc.status_code,
            message=message,
            details=details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors"""
        return _json_error_response(
            status_code=_HTTP_422,
            message="Validation error",
            details=exc.errors(),
            error_code="VALIDATION_ERROR",
        )

    @app.exception_handler(RepositoryError)
    async def repository_exception_handler(request: Request, exc: RepositoryError):
        """Handle persistence layer errors"""
        logger.warning("Repository failure on %s %s: %s", request.method, request.url.path, exc)
        return _json_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=str(exc) or "Persistence unavailable",
            error_code="SERVICE_UNAVAILABLE",
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions"""
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _json_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            error_code="INTERNAL_SERVER_ERROR",
        )


def register_error_middleware(app: FastAPI) -> None:
    """Register error standardization middleware"""
    app.add_middleware(ErrorStandardizationMiddleware)
