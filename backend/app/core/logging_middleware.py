"""Structured logging and ``X-Request-ID`` correlation middleware.

Every request gets a unique ``X-Request-ID`` (generated here when the caller
did not provide one) that is:

- stored in a ``contextvars`` ``ContextVar`` so every log record produced
  while serving the request carries the id (middleware, routes, services),
- mirrored on the response header so clients and support teams can correlate
  logs with a single HTTP request.

The ``JsonFormatter`` outputs one JSON object per line (stdlib only) and
``ReadableFormatter`` is a human-friendly alternative for development.
"""

from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("arpia.api")

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for machine consumption.

    Outputs: ``ts`` (ISO-8601 UTC), ``level``, ``logger``, ``message`` plus the
    request context (``request_id``, ``method``, ``path``, ``status_code``)
    when present, either as ``extra`` on the record or via the ``request_id``
    ``ContextVar``. ``exc_info`` is rendered as ``exc_info`` when set.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        for field in ("method", "path", "status_code"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """Human-friendly layout for development, still exposing the request_id."""

    def __init__(self) -> None:
        super().__init__(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        context = " ".join(
            str(getattr(record, field, None))
            for field in ("method", "path", "status_code")
            if getattr(record, field, None) is not None
        )
        line = super().format(record)
        if request_id:
            line += f" [req={request_id}]"
        if context:
            line += f" ({context})"
        return line


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach an ``X-Request-ID`` to every request and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            request_id_var.reset(token)
