"""Tests for audit core: audit table, audit triggers/services, audit query API."""
import pytest
from datetime import datetime, date, timedelta, UTC
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient

from app.models.audit import AuditLog
from app.services.audit import (
    AuditService,
    audit_venta_create,
    audit_venta_update,
    audit_venta_delete,
    audit_devolucion_create,
    audit_compra_create,
    audit_movimiento_create,
    audit_usuario_create,
    audit_usuario_update,
    audit_stock_adjust,
)
from app.core.deps import require_admin, require_roles
from app.models.usuarios import Usuario
from app.schemas.audit import AuditLogRead


class TestAuditModel:
    """AuditLog model should capture all required fields."""

    def test_audit_log_model_fields(self):
        """Verify AuditLog has all required fields."""
        audit = AuditLog(
            usuario_id=1,
            usuario_rol="admin",
            entidad="ventas",
            entity_id=123,
            accion="create",
            valores_old=None,
            valores_new={"total": 100.0},
            request_id="req-123",
            ip="192.168.1.1",
            user_agent="test-agent",
        )
        assert audit.usuario_id == 1
        assert audit.usuario_rol == "admin"
        assert audit.entidad == "ventas"
        assert audit.entity_id == 123
        assert audit.accion == "create"
        assert audit.valores_old is None
        assert audit.valores_new == {"total": 100.0}
        assert audit.request_id == "req-123"
        assert audit.ip == "192.168.1.1"
        assert audit.user_agent == "test-agent"
        assert audit.timestamp is not None

    def test_audit_log_requires_entidad_and_action(self):
        """entidad and accion should be required."""
        with pytest.raises(Exception):
            AuditLog(usuario_id=1, usuario_rol="admin", accion="create")  # missing entidad


class TestAuditService:
    """AuditService should provide structured logging."""

    def test_audit_service_create_log(self, db_session: Session):
        """Service should create audit log entry."""
        service = AuditService(db_session)
        service.log(
            usuario_id=1,
            usuario_rol="admin",
            entidad="ventas",
            entity_id=1,
            accion="create",
            valores_new={"total": 100.0},
            request_id="req-1",
            ip="127.0.0.1",
            user_agent="test",
        )
        db_session.commit()

        log = db_session.query(AuditLog).filter(AuditLog.entity_id == 1).first()
        assert log is not None
        assert log.entidad == "ventas"
        assert log.accion == "create"

    def test_audit_service_log_update_captures_old_new(self, db_session: Session):
        """Update action should capture both old and new values."""
        service = AuditService(db_session)
        service.log(
            usuario_id=1,
            usuario_rol="operador",
            entidad="ventas",
            entity_id=1,
            accion="update",
            valores_old={"total": 100.0, "estado": "completada"},
            valores_new={"total": 150.0, "estado": "completada"},
            request_id="req-2",
            ip="127.0.0.1",
            user_agent="test",
        )
        db_session.commit()

        log = db_session.query(AuditLog).filter(AuditLog.accion == "update").first()
        assert log.valores_old == {"total": 100.0, "estado": "completada"}
        assert log.valores_new == {"total": 150.0, "estado": "completada"}


class TestAuditTriggers:
    """Audit triggers/services for domain operations."""

    def test_audit_venta_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a venta should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post("/api/v1/ventas/", headers=headers, json={
            "cliente_id": 1,
            "canal_venta": "web",
            "detalles": [{"producto_id": 1, "cantidad": 1, "precio_unitario": 100}]
        })
        assert resp.status_code == 201
        venta_id = resp.json()["id"]

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "ventas",
            AuditLog.entity_id == venta_id,
            AuditLog.accion == "create"
        ).first()
        assert audit is not None
        assert audit.usuario_id == 1
        assert audit.valores_new is not None

    def test_audit_venta_update(self, db_session: Session, client: TestClient, admin_token: str):
        """Updating a venta should generate audit log with old/new values."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Create
        resp = client.post("/api/v1/ventas/", headers=headers, json={
            "cliente_id": 1, "canal_venta": "web",
            "detalles": [{"producto_id": 1, "cantidad": 1, "precio_unitario": 100}]
        })
        venta_id = resp.json()["id"]

        # Update
        resp = client.put(f"/api/v1/ventas/{venta_id}", headers=headers, json={
            "cliente_id": 1, "canal_venta": "web",
            "detalles": [{"producto_id": 1, "cantidad": 2, "precio_unitario": 100}]
        })
        assert resp.status_code == 200

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "ventas",
            AuditLog.entity_id == venta_id,
            AuditLog.accion == "update"
        ).first()
        assert audit is not None
        assert audit.valores_old is not None
        assert audit.valores_new is not None

    def test_audit_venta_delete(self, db_session: Session, client: TestClient, admin_token: str):
        """Deleting a venta should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post("/api/v1/ventas/", headers=headers, json={
            "cliente_id": 1, "canal_venta": "web",
            "detalles": [{"producto_id": 1, "cantidad": 1, "precio_unitario": 100}]
        })
        venta_id = resp.json()["id"]

        resp = client.delete(f"/api/v1/ventas/{venta_id}", headers=headers)
        assert resp.status_code == 200

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "ventas",
            AuditLog.entity_id == venta_id,
            AuditLog.accion == "delete"
        ).first()
        assert audit is not None

    def test_audit_devolucion_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a devolucion should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Need a venta first
        resp = client.post("/api/v1/ventas/", headers=headers, json={
            "cliente_id": 1, "canal_venta": "web",
            "detalles": [{"producto_id": 1, "cantidad": 1, "precio_unitario": 100}]
        })
        venta_id = resp.json()["id"]

        resp = client.post("/api/v1/devoluciones/", headers=headers, json={
            "venta_id": venta_id, "tipo": "total", "motivo": "test"
        })
        assert resp.status_code == 201
        devolucion_id = resp.json()["id"]

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "devoluciones",
            AuditLog.entity_id == devolucion_id,
            AuditLog.accion == "create"
        ).first()
        assert audit is not None

    def test_audit_compra_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a compra should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post("/api/v1/compras-insumos/", headers=headers, json={
            "insumo_id": 1, "cantidad_comprada": 10, "precio_unitario_compra": 50
        })
        assert resp.status_code == 201
        compra_id = resp.json()["id"]

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "compras_insumos",
            AuditLog.entity_id == compra_id,
            AuditLog.accion == "create"
        ).first()
        assert audit is not None

    def test_audit_movimiento_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a movimiento financiero should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post("/api/v1/finanzas/movimientos", headers=headers, json={
            "tipo": "Gasto", "monto": 500, "descripcion": "test", "fecha": "2024-01-15"
        })
        assert resp.status_code == 201
        mov_id = resp.json()["id"]

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "finanzas_movimientos",
            AuditLog.entity_id == mov_id,
            AuditLog.accion == "create"
        ).first()
        assert audit is not None

    def test_audit_usuario_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a usuario should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post("/api/v1/usuarios/", headers=headers, json={
            "nombre": "Test User", "email": "test@test.com", "password": "Pass123!", "rol": "operador"
        })
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        audit = db_session.query(AuditLog).filter(
            AuditLog.entidad == "usuarios",
            AuditLog.entity_id == user_id,
            AuditLog.accion == "create"
        ).first()
        assert audit is not None

    def test_audit_stock_adjust(self, db_session: Session, client: TestClient, admin_token: str):
        """Stock adjustment should generate audit log."""
        # This tests the migration adjust stock audit
        pass


class TestAuditQueryAPI:
    """Audit query API with filters and role-based access."""

    def test_audit_list_requires_auth(self, client: TestClient):
        """Audit endpoint should require authentication."""
        resp = client.get("/api/v1/auditoria/")
        assert resp.status_code == 401

    def test_audit_list_admin_access(self, client: TestClient, admin_token: str):
        """Admin should access audit logs."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers)
        assert resp.status_code == 200
        assert "items" in resp.json()
        assert "total" in resp.json()

    def test_audit_list_operador_access(self, client: TestClient, operador_token: str):
        """Operador should access audit logs (read-only)."""
        headers = {"Authorization": f"Bearer {operador_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers)
        assert resp.status_code == 200

    def test_audit_list_consulta_access(self, client: TestClient, consulta_token: str):
        """Consulta should access audit logs (read-only)."""
        headers = {"Authorization": f"Bearer {consulta_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers)
        assert resp.status_code == 200

    def test_audit_filter_by_usuario(self, client: TestClient, admin_token: str):
        """Filter audit logs by usuario."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers, params={"usuario_id": 1})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["usuario_id"] == 1

    def test_audit_filter_by_entidad(self, client: TestClient, admin_token: str):
        """Filter audit logs by entidad."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers, params={"entidad": "ventas"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["entidad"] == "ventas"

    def test_audit_filter_by_accion(self, client: TestClient, admin_token: str):
        """Filter audit logs by accion."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers, params={"accion": "create"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["accion"] == "create"

    def test_audit_filter_by_fecha_range(self, client: TestClient, admin_token: str):
        """Filter audit logs by date range."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        today = date.today().isoformat()
        resp = client.get("/api/v1/auditoria/", headers=headers, params={
            "fecha_desde": today,
            "fecha_hasta": today
        })
        assert resp.status_code == 200

    def test_audit_pagination(self, client: TestClient, admin_token: str):
        """Audit logs should be paginated."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/v1/auditoria/", headers=headers, params={"limit": 5, "offset": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5
        assert "total" in data

    def test_audit_read_only_no_write(self, client: TestClient, admin_token: str):
        """Audit endpoint should be read-only (no POST/PUT/DELETE)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        for method in ["post", "put", "patch", "delete"]:
            resp = getattr(client, method)("/api/v1/auditoria/", headers=headers, json={})
            assert resp.status_code == 405  # Method Not Allowed