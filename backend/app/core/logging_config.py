"""One-time logging bootstrap for the FastAPI application.

Called from ``app.main`` at import time. Development uses a readable,
request-id-anchored text format on stderr; staging/production emit pure JSON
for machine aggregation. No third-party dependencies beyond the stdlib.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import settings
from app.core.logging_middleware import JsonFormatter, ReadableFormatter


def setup_logging(environment: str | None = None) -> None:
    env = (environment or settings.ENVIRONMENT).lower()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if env != "development" else ReadableFormatter())
    # Marker so re-installs are idempotent without touching third-party
    # handlers (e.g. pytest's caplog LogCaptureHandler on the root logger).
    handler._arpia_logging_handler = True  # type: ignore[attr-defined]

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for existing in list(root.handlers):
        if getattr(existing, "_arpia_logging_handler", False):
            root.removeHandler(existing)
    root.addHandler(handler)

    # Ensure the app namespace never sinks below INFO regardless of the root.
    logging.getLogger("arpia.api").setLevel(logging.INFO)
