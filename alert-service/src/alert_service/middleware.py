"""
HTTP middlewares for the alert service.

Currently exposes:

* :class:`TraceIdMiddleware` — extracts the ``X-Trace-Id`` header from
  incoming requests (or generates a new UUID v4 if absent) and propagates
  it to the response. The same id is then attached to ``request.state``
  so handlers can include it in error payloads and structured logs.
"""

from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

TRACE_ID_HEADER = "X-Trace-Id"


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    Propagate a ``trace_id`` for every HTTP request.

    Resolution order:
        1. ``X-Trace-Id`` header sent by the client (preferred).
        2. UUID v4 generated server-side.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())

        # Expose to handlers via request.state
        request.state.trace_id = trace_id

        logger.debug(
            "request.start method=%s path=%s trace_id=%s",
            request.method,
            request.url.path,
            trace_id,
        )

        response = await call_next(request)

        # Echo the trace_id back to the client so they can quote it in
        # support tickets and we can correlate end-to-end.
        response.headers[TRACE_ID_HEADER] = trace_id

        logger.debug(
            "request.end method=%s path=%s status=%d trace_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            trace_id,
        )

        return response
