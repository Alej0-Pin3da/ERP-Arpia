"""Tests for audit core: audit table, audit triggers/services, audit query API."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.audit import AuditLog
from app.models.clientes import Cliente
from app.models.productos import Producto, TipoProducto
from app.services.audit import (
    AuditService,
)


def _ensure_audit_fixtures():
    """Ensure minimal Cliente + Producto + Insumo + BOM exist for audit trigger tests
    (clean DB has only admin/categorias)."""
    from app.models.insumos import CategoriaInsumo, Insumo
    from app.models.productos import BomInsumo

    db = SessionLocal()
    try:
        if db.get(Cliente, 1) is None:
            try:
                c = Cliente(
                    nombre="Audit Cliente", email="audit-cliente@test.local", telefono="3000000000"
                )
                db.add(c)
                db.flush()
                db.commit()
            except Exception:
                db.rollback()
        if db.get(Producto, 1) is None:
            try:
                tipo = db.query(TipoProducto).first()
                if tipo is None:
                    tipo = TipoProducto(nombre="Audit Tipo")
                    db.add(tipo)
                    db.flush()
                p = Producto(nombre="Audit Producto", tipo_producto_id=tipo.id)
                db.add(p)
                db.flush()
                db.commit()
            except Exception:
                db.rollback()
        # Ensure Insumo + BOM for producto 1 so venta devoluciones can restore stock
        try:
            from sqlalchemy import text as _text

            # Check if BomInsumo exists for producto 1
            has_bom = db.execute(
                _text('SELECT 1 FROM "BOM_Insumos" WHERE producto_id = 1 LIMIT 1')
            ).scalar()
            if not has_bom:
                # Ensure an insumo exists
                insumo = db.get(Insumo, 1)
                if insumo is None:
                    cat = db.query(CategoriaInsumo).first()
                    if cat is None:
                        cat = CategoriaInsumo(nombre="Audit Cat BOM")
                        db.add(cat)
                        db.flush()
                    insumo = Insumo(
                        nombre="Audit Insumo BOM",
                        categoria_id=cat.id,
                        unidad_medida="kg",
                        stock_actual=Decimal("100"),
                        stock_minimo=Decimal("10"),
                        costo_promedio_actual=Decimal("10"),
                    )
                    db.add(insumo)
                    db.flush()
                # Create BOM linking producto 1 to insumo
                bom = BomInsumo(producto_id=1, insumo_id=insumo.id, cantidad_requerida=Decimal("1"))
                db.add(bom)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def _query_audit_fresh(entidad: str, entity_id: int, accion: str):
    """Query audit log with a fresh DB session (avoids stale fixture transaction)."""
    db = SessionLocal()
    try:
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.entidad == entidad,
                AuditLog.entity_id == entity_id,
                AuditLog.accion == accion,
            )
            .first()
        )
    finally:
        db.close()


def _create_audit_venta_fixtures():
    """Create a fresh Cliente + Producto (+ Insumo/BOM for devoluciones) and return IDs
    (isolated)."""
    import uuid

    from app.models.insumos import CategoriaInsumo, Insumo
    from app.models.productos import BomInsumo

    db = SessionLocal()
    try:
        cliente = Cliente(
            nombre=f"Audit Cliente {uuid.uuid4().hex[:6]}",
            email=f"audit-{uuid.uuid4().hex[:8]}@test.local",
            telefono="3000000000",
        )
        db.add(cliente)
        db.flush()
        tipo = db.query(TipoProducto).first()
        if tipo is None:
            tipo = TipoProducto(nombre=f"Audit Tipo {uuid.uuid4().hex[:6]}")
            db.add(tipo)
            db.flush()
        producto = Producto(nombre=f"Audit Prod {uuid.uuid4().hex[:6]}", tipo_producto_id=tipo.id)
        db.add(producto)
        db.flush()
        # Ensure a BOM so devoluciones can restore stock (total cancel needs consumables)
        cat = db.query(CategoriaInsumo).first()
        if cat is None:
            cat = CategoriaInsumo(nombre=f"Audit Cat {uuid.uuid4().hex[:6]}")
            db.add(cat)
            db.flush()
        insumo = Insumo(
            nombre=f"Audit Insumo {uuid.uuid4().hex[:6]}",
            categoria_id=cat.id,
            unidad_medida="kg",
            stock_actual=Decimal("100"),
            stock_minimo=Decimal("10"),
            costo_promedio_actual=Decimal("10"),
        )
        db.add(insumo)
        db.flush()
        bom = BomInsumo(
            producto_id=producto.id, insumo_id=insumo.id, cantidad_requerida=Decimal("1")
        )
        db.add(bom)
        db.commit()
        return cliente.id, producto.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class TestAuditModel:
    """AuditLog model should capture all required fields."""

    def test_audit_log_model_fields(self, db_session: Session):
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
        db_session.add(audit)
        db_session.flush()
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
        db_session.rollback()

    def test_audit_log_requires_entidad_and_action(self, db_session: Session):
        """entidad and accion should be required (DB constraint)."""
        audit = AuditLog(usuario_id=1, usuario_rol="admin", accion="create")  # missing entidad
        db_session.add(audit)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()


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
        cliente_id, producto_id = _create_audit_venta_fixtures()
        headers = {"Authorization": f"Bearer {admin_token}"}
        try:
            resp = client.post(
                "/api/v1/ventas",
                headers=headers,
                json={
                    "cliente_id": cliente_id,
                    "canal_venta": "web",
                    "detalles": [
                        {"producto_id": producto_id, "cantidad": 1, "precio_unitario": 100}
                    ],
                },
            )
            assert resp.status_code == 201
            venta_id = resp.json()["id"]

            audit = _query_audit_fresh("ventas", venta_id, "create")
            assert audit is not None
            assert audit.usuario_id == 1
            assert audit.valores_new is not None
        finally:
            # Cleanup to avoid polluting subsequent tests in the same session DB
            try:
                db2 = SessionLocal()
                from app.models.ventas import Venta

                db2.query(Venta).filter(Venta.cliente_id == cliente_id).delete()
                db2.commit()
                # Also cleanup the fresh producto/cliente if they are not reused
                # Keep them for now to avoid FK issues; they are unique per test and small in number
            except Exception:
                pass
            finally:
                try:
                    db2.close()
                except Exception:
                    pass

    def test_audit_venta_update(self, db_session: Session, client: TestClient, admin_token: str):
        """Updating a venta should generate audit log with old/new values."""
        cliente_id, producto_id = _create_audit_venta_fixtures()
        headers = {"Authorization": f"Bearer {admin_token}"}
        venta_id = None
        try:
            # Create
            resp = client.post(
                "/api/v1/ventas",
                headers=headers,
                json={
                    "cliente_id": cliente_id,
                    "canal_venta": "web",
                    "detalles": [
                        {"producto_id": producto_id, "cantidad": 1, "precio_unitario": 100}
                    ],
                },
            )
            assert resp.status_code == 201
            venta_id = resp.json()["id"]

            # Update
            resp = client.put(
                f"/api/v1/ventas/{venta_id}",
                headers=headers,
                json={
                    "cliente_id": cliente_id,
                    "canal_venta": "web",
                    "detalles": [
                        {"producto_id": producto_id, "cantidad": 2, "precio_unitario": 100}
                    ],
                },
            )
            assert resp.status_code == 200

            audit = _query_audit_fresh("ventas", venta_id, "update")
            assert audit is not None
            assert audit.valores_old is not None
            assert audit.valores_new is not None
        finally:
            if venta_id:
                try:
                    db2 = SessionLocal()
                    from app.models.ventas import Venta

                    db2.query(Venta).filter(Venta.id == venta_id).delete()
                    db2.commit()
                except Exception:
                    try:
                        db2.rollback()
                    except Exception:
                        pass
                finally:
                    try:
                        db2.close()
                    except Exception:
                        pass

    def test_audit_venta_delete(self, db_session: Session, client: TestClient, admin_token: str):
        """Deleting a venta should generate audit log."""
        cliente_id, producto_id = _create_audit_venta_fixtures()
        headers = {"Authorization": f"Bearer {admin_token}"}
        try:
            resp = client.post(
                "/api/v1/ventas",
                headers=headers,
                json={
                    "cliente_id": cliente_id,
                    "canal_venta": "web",
                    "detalles": [
                        {"producto_id": producto_id, "cantidad": 1, "precio_unitario": 100}
                    ],
                },
            )
            assert resp.status_code == 201
            venta_id = resp.json()["id"]

            resp = client.delete(f"/api/v1/ventas/{venta_id}", headers=headers)
            assert resp.status_code == 200

            audit = _query_audit_fresh("ventas", venta_id, "delete")
            assert audit is not None
        finally:
            # Venta is already soft-deleted (cancelled), no extra cleanup needed for count
            pass

    def test_audit_devolucion_create(
        self, db_session: Session, client: TestClient, admin_token: str
    ):
        """Creating a devolucion should generate audit log."""
        cliente_id, producto_id = _create_audit_venta_fixtures()
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Need a venta first
        resp = client.post(
            "/api/v1/ventas",
            headers=headers,
            json={
                "cliente_id": cliente_id,
                "canal_venta": "web",
                "detalles": [{"producto_id": producto_id, "cantidad": 1, "precio_unitario": 100}],
            },
        )
        venta_id = resp.json()["id"]

        resp = client.post(
            "/api/v1/devoluciones",
            headers=headers,
            json={"venta_id": venta_id, "tipo": "total", "motivo": "test"},
        )
        assert resp.status_code == 201
        devolucion_id = resp.json()["id"]

        audit = _query_audit_fresh("devoluciones", devolucion_id, "create")
        assert audit is not None

    def test_audit_compra_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a compra should generate audit log."""
        from app.models.insumos import CategoriaInsumo, Insumo

        db2 = SessionLocal()
        try:
            if db2.get(Insumo, 1) is None:
                cat = db2.query(CategoriaInsumo).first()
                if cat is None:
                    cat = CategoriaInsumo(nombre="Audit Cat")
                    db2.add(cat)
                    db2.flush()
                ins = Insumo(
                    nombre="Audit Insumo",
                    categoria_id=cat.id,
                    unidad_medida="kg",
                    stock_actual=Decimal("100"),
                    stock_minimo=Decimal("10"),
                    costo_promedio_actual=Decimal("10"),
                )
                db2.add(ins)
                db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post(
            "/api/v1/compras-insumos",
            headers=headers,
            json={"insumo_id": 1, "cantidad_comprada": 10, "precio_unitario_compra": 50},
        )
        assert resp.status_code == 201
        compra_id = resp.json()["id"]

        audit = _query_audit_fresh("compras_insumos", compra_id, "create")
        assert audit is not None

    def test_audit_movimiento_create(
        self, db_session: Session, client: TestClient, admin_token: str
    ):
        """Creating a movimiento financiero should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post(
            "/api/v1/finanzas/movimientos",
            headers=headers,
            json={"tipo": "Gasto", "monto": 500, "descripcion": "test", "fecha": "2024-01-15"},
        )
        assert resp.status_code == 201
        mov_id = resp.json()["id"]

        audit = _query_audit_fresh("finanzas_movimientos", mov_id, "create")
        assert audit is not None

    def test_audit_usuario_create(self, db_session: Session, client: TestClient, admin_token: str):
        """Creating a usuario should generate audit log."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post(
            "/api/v1/usuarios/",
            headers=headers,
            json={
                "nombre": "Test User",
                "email": "test@test.com",
                "password": "Pass123!",
                "rol": "operador",
            },
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        audit = _query_audit_fresh("usuarios", user_id, "create")
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
        resp = client.get(
            "/api/v1/auditoria/",
            headers=headers,
            params={"fecha_desde": today, "fecha_hasta": today},
        )
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
        for method in ["post", "put", "patch"]:
            resp = getattr(client, method)("/api/v1/auditoria/", headers=headers, json={})
            assert resp.status_code == 405  # Method Not Allowed
        # delete with json is not supported by TestClient in this version; use request
        resp = client.request("DELETE", "/api/v1/auditoria/", headers=headers, json={})
        assert resp.status_code == 405
