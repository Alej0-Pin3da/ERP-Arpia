"""Tests for the X-Request-ID correlation middleware — no database required.

Uses ``/api/v1/openapi.json`` (schema endpoint) which never touches the database.

The log assertions attach their own handler to the ``arpia.api`` logger instead
of relying on ``caplog`` because the app's ``setup_logging()`` and pytest's
logging plugin both reconfigure the root logger level during a session.
"""

import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _capture_logs() -> tuple[list[logging.LogRecord], logging.Handler]:
    captured: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    handler = CaptureHandler(level=logging.INFO)
    logger = logging.getLogger("arpia.api")
    logger.addHandler(handler)
    return captured, handler


def test_response_has_x_request_id_header():
    resp = client.get("/api/v1/openapi.json")
    assert resp.status_code == 200
    request_id = resp.headers.get("X-Request-ID")
    assert request_id
    assert len(request_id) == 16


def test_incoming_request_id_is_echoed():
    resp = client.get("/api/v1/openapi.json", headers={"X-Request-ID": "custom-trace-123"})
    assert resp.headers["X-Request-ID"] == "custom-trace-123"


def test_request_id_appears_in_logs():
    captured, handler = _capture_logs()
    try:
        resp = client.get("/api/v1/openapi.json")
    finally:
        logging.getLogger("arpia.api").removeHandler(handler)
    request_id = resp.headers["X-Request-ID"]
    assert request_id
    assert any(getattr(record, "request_id", None) == request_id for record in captured)


def test_json_formatter_emits_request_fields():
    captured, handler = _capture_logs()
    try:
        resp = client.get("/api/v1/openapi.json")
    finally:
        logging.getLogger("arpia.api").removeHandler(handler)
    request_id = resp.headers["X-Request-ID"]
    record = next(r for r in captured if getattr(r, "request_id", None) == request_id)
    assert record.method == "GET"
    assert record.path == "/api/v1/openapi.json"
    assert record.status_code == 200
