"""Tests for idempotency middleware."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestIdempotencyMiddleware:
    """Test idempotency key handling for critical endpoints."""

    def test_idempotency_key_required_for_ventas_post(self, client: TestClient):
        """POST /api/v1/ventas requires Idempotency-Key header."""
        resp = client.post(
            "/api/v1/ventas",
            json={
                "cliente_id": 1,
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "es_regalo": False,
                "detalles": [{"producto_id": 1, "cantidad": "1", "precio_unitario": "100"}],
            },
        )
        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    def test_idempotency_key_required_for_devoluciones_post(self, client: TestClient):
        """POST /api/v1/devoluciones requires Idempotency-Key header."""
        resp = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": 1, "tipo": "total", "motivo": "test"},
        )
        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    def test_idempotency_key_required_for_compras_post(self, client: TestClient):
        """POST /api/v1/compras requires Idempotency-Key header."""
        resp = client.post(
            "/api/v1/compras",
            json={"insumo_id": 1, "cantidad_comprada": "10", "precio_unitario_compra": "50"},
        )
        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    def test_idempotency_key_required_for_movimientos_post(self, client: TestClient):
        """POST /api/v1/finanzas/movimientos requires Idempotency-Key header."""
        resp = client.post(
            "/api/v1/finanzas/movimientos",
            json={"tipo": "Gasto", "descripcion": "Test", "monto": "100"},
        )
        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    def test_idempotency_key_valid_format_accepted(self, client: TestClient):
        """Valid UUID-like idempotency key is accepted."""
        # This will fail with 422/404 due to missing data, but NOT 400 for missing key
        resp = client.post(
            "/api/v1/ventas",
            headers={"Idempotency-Key": "550e8400-e29b-41d4-a716-446655440000"},
            json={
                "cliente_id": 1,
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "es_regalo": False,
                "detalles": [{"producto_id": 1, "cantidad": "1", "precio_unitario": "100"}],
            },
        )
        # Should not be 400 for missing idempotency key
        assert resp.status_code != 400 or "Idempotency-Key" not in resp.json().get("detail", "")

    def test_idempotency_key_invalid_format_rejected(self, client: TestClient):
        """Invalid idempotency key format is rejected."""
        resp = client.post(
            "/api/v1/ventas",
            headers={"Idempotency-Key": "invalid key with spaces"},
            json={
                "cliente_id": 1,
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "es_regalo": False,
                "detalles": [{"producto_id": 1, "cantidad": "1", "precio_unitario": "100"}],
            },
        )
        assert resp.status_code == 400
        assert "Invalid Idempotency-Key format" in resp.json()["detail"]

    def test_idempotency_key_too_short_rejected(self, client: TestClient):
        """Too short idempotency key is rejected."""
        resp = client.post(
            "/api/v1/ventas",
            headers={"Idempotency-Key": "short"},
            json={
                "cliente_id": 1,
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "es_regalo": False,
                "detalles": [{"producto_id": 1, "cantidad": "1", "precio_unitario": "100"}],
            },
        )
        assert resp.status_code == 400
        assert "Invalid Idempotency-Key format" in resp.json()["detail"]

    def test_get_requests_not_require_idempotency(self, client: TestClient):
        """GET requests don't require idempotency key."""
        resp = client.get("/api/v1/ventas")
        # Should not fail due to missing idempotency key
        assert resp.status_code != 400 or "Idempotency-Key" not in resp.json().get("detail", "")

    def test_idempotency_key_returned_in_response_headers(self, client: TestClient):
        """Idempotency-Key is echoed back in response headers."""
        resp = client.post(
            "/api/v1/ventas",
            headers={"Idempotency-Key": "550e8400-e29b-41d4-a716-446655440000"},
            json={
                "cliente_id": 1,
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "es_regalo": False,
                "detalles": [{"producto_id": 1, "cantidad": "1", "precio_unitario": "100"}],
            },
        )
        # The key should be echoed back (even if request fails for other reasons)
        if resp.status_code < 500:
            assert resp.headers.get("Idempotency-Key") == "550e8400-e29b-41d4-a716-446655440000"

    def test_middleware_registered_in_app(self):
        """Verify idempotency middleware is registered in the app."""
        from app.main import app
        middleware_names = [m.cls.__name__ for m in app.user_middleware]
        assert "ConfiguredIdempotencyMiddleware" in str(middleware_names) or any(
            "idempotency" in str(m).lower() for m in app.user_middleware
        )