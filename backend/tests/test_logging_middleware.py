"""Tests for the X-Request-ID correlation middleware — no database required.

Uses ``/api/v1/openapi.json`` (schema endpoint) which never touches the database.
"""

import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_response_has_x_request_id_header():
    resp = client.get("/api/v1/openapi.json")
    assert resp.status_code == 200
    request_id = resp.headers.get("X-Request-ID")
    assert request_id
    assert len(request_id) == 16


def test_incoming_request_id_is_echoed():
    resp = client.get("/api/v1/openapi.json", headers={"X-Request-ID": "custom-trace-123"})
    assert resp.headers["X-Request-ID"] == "custom-trace-123"


def test_request_id_appears_in_logs(caplog):
    with caplog.at_level(logging.INFO, logger="arpia.api"):
        resp = client.get("/api/v1/openapi.json")
    request_id = resp.headers["X-Request-ID"]
    assert request_id
    assert any(getattr(record, "request_id", None) == request_id for record in caplog.records)


def test_json_formatter_emits_request_fields(caplog):
    with caplog.at_level(logging.INFO, logger="arpia.api"):
        resp = client.get("/api/v1/openapi.json")
    request_id = resp.headers["X-Request-ID"]
    record = next(r for r in caplog.records if getattr(r, "request_id", None) == request_id)
    assert record.method == "GET"
    assert record.path == "/api/v1/openapi.json"
    assert record.status_code == 200
