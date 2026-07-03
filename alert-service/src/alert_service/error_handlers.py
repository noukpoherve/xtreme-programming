"""
Centralized FastAPI exception handlers.

Every error raised by the application — domain, validation, or unexpected —
is converted into a uniform :class:`ErrorResponse` JSON payload.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from alert_service.exceptions import AlertServiceError
from alert_service.models import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def _trace_id(request: Request) -> str:
    """Return the request's trace_id, generating one if absent."""
    return getattr(request.state, "trace_id", None) or str(uuid.uuid4())


def _build_error_response(
    *,
    request: Request,
    error_code: ErrorCode,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    """
    Build the canonical JSON error response.

    The trace_id stored in ``request.state`` (set by the middleware) is
    included so that operators can correlate the response with logs.
    """
    payload = ErrorResponse(
        error=error_code,
        message=message,
        trace_id=_trace_id(request),
        timestamp=datetime.now(timezone.utc),
        path=request.url.path,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers={"X-Trace-Id": _trace_id(request)},
    )


# ──────────────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────────────
async def alert_service_error_handler(
    request: Request, exc: AlertServiceError
) -> JSONResponse:
    """Handle every custom domain exception raised by the service."""

    # Map our internal error code to the public ErrorCode enum. If a
    # subclass forgets to set error_code, we fall back to INTERNAL_ERROR.
    try:
        public_code = ErrorCode(exc.error_code)
    except ValueError:
        public_code = ErrorCode.INTERNAL_ERROR
        logger.warning(
            "Unknown error_code %s on %s; falling back to INTERNAL_ERROR",
            exc.error_code,
            exc.__class__.__name__,
        )

    logger.warning(
        "Domain error: code=%s status=%d trace_id=%s path=%s message=%s",
        public_code.value,
        exc.http_status,
        _trace_id(request),
        request.url.path,
        exc.message,
    )

    return _build_error_response(
        request=request,
        error_code=public_code,
        message=exc.message,
        status_code=exc.http_status,
        details=exc.details or None,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic / FastAPI request validation errors.

    Pydantic returns 422 by default. We keep that status but rewrap the
    raw errors in our standard envelope so that clients can parse every
    error response with a single schema.
    """
    # Each error from Pydantic is a dict; we trim it to the essentials
    # so we don't leak internal paths.
    sanitized = [
        {
            "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]

    return _build_error_response(
        request=request,
        error_code=ErrorCode.VALIDATION_ERROR,
        message="One or more fields failed validation.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": sanitized},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle plain HTTPExceptions raised manually (404, 405, etc.)."""

    # Map the HTTP status to the most relevant ErrorCode. We keep a
    # simple lookup so the contract stays predictable.
    status_to_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.VALIDATION_ERROR,
        403: ErrorCode.VALIDATION_ERROR,
        404: ErrorCode.SENSOR_NOT_FOUND,
        405: ErrorCode.VALIDATION_ERROR,
        409: ErrorCode.INVALID_STATE_TRANSITION,
    }
    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    return _build_error_response(
        request=request,
        error_code=error_code,
        message=str(exc.detail) if exc.detail else "HTTP error.",
        status_code=exc.status_code,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for any exception not caught by a more specific one."""

    logger.exception(
        "Unhandled exception trace_id=%s path=%s",
        _trace_id(request),
        request.url.path,
    )

    return _build_error_response(
        request=request,
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred. Please contact support with the trace_id.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ──────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────
def register_error_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to a FastAPI app instance."""

    app.add_exception_handler(AlertServiceError, alert_service_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
