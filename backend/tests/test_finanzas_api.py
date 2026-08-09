"""Finanzas API endpoint tests — strict TDD (slice 3, task 3.1).

Drives the finanzas HTTP surface through the FastAPI TestClient against the
real test PostgreSQL:
- POST/GET/DELETE /finanzas/movimientos: 201 create with Decimal monto, soft
  delete (estado inactivo, excluded from list), 404 on unknown id, 422 on
  invalid tipo (FIN-1).
- POST /finanzas/liquidaciones: one-time proportional settlement across socios
  (per-socio Retiro rows = monto * % / 100); replay of the same liquidacion_id
  -> 409, no duplicated payouts (FIN-1).
- POST/PATCH/DELETE /finanzas/socios: sum-to-100 on create (99/101 -> 422),
  interim rebalance allowed on update, delete blocked 409 when the socio has
  payouts (FIN-2).
- 401 without token; consulta -> 403 on any mutation, 200 on lists.

The sum-to-100 invariant is GLOBAL across the shared DB, so the module wipes
Movimientos_Financieros + Socios_Configuracion at start (same contract as the
engine test_finanzas.py) to keep the boundary assertions deterministic.
"""

import uuid
from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models import MovimientoFinanciero, SociosConfiguracion


def _unique() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture(scope="module", autouse=True)
def _finanzas_api_tablas_limpias():
    """Start the module with no partner rows / movements (see module docstring).

    La DB real puede tener la MIGRACION cargada (3 socios canonicos 40/30/30 +
    sus movimientos): ese estado se RESPALDA antes de limpiar y se RESTAURA al
    final del modulo (patron: nunca borrar la migracion cargada)."""
    db = SessionLocal()
    try:
        socios = [
            (s.id, s.nombre, s.porcentaje_participacion)
            for s in db.query(SociosConfiguracion).all()
        ]
        movs = [
            (m.id, m.fecha, m.tipo, m.descripcion, m.monto, m.socio_id,
             m.estado, m.liquidacion_id)
            for m in db.query(MovimientoFinanciero).all()
        ]
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
        yield
        # Restaurar el estado pre-modulo (filas de la migracion u otros modulos).
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
        for sid, nombre, pct in socios:
            db.add(SociosConfiguracion(
                id=sid, nombre=nombre, porcentaje_participacion=pct
            ))
        db.commit()
        for mid, fecha, tipo, desc, monto, socio_id, estado, liq in movs:
            db.add(MovimientoFinanciero(
                id=mid, fecha=fecha, tipo=tipo, descripcion=desc, monto=monto,
                socio_id=socio_id, estado=estado, liquidacion_id=liq,
            ))
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _movimiento_payload(tipo: str = "Gasto", monto: str = "10", socio_id: int | None = None) -> dict:
    return {
        "tipo": tipo,
        "descripcion": f"Movimiento {_unique()}",
        "monto": monto,
        "socio_id": socio_id,
    }


def _crear_socio(client, token: str, porcentaje: str, nombre: str | None = None) -> int:
    resp = client.post(
        "/api/v1/finanzas/socios",
        json={"nombre": nombre or f"Socio {_unique()}", "porcentaje_participacion": porcentaje},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _actualizar_socio(client, token: str, socio_id: int, porcentaje: str) -> int:
    resp = client.patch(
        f"/api/v1/finanzas/socios/{socio_id}",
        json={"porcentaje_participacion": porcentaje},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.status_code


def _crear_socios_60_40(client, token: str) -> tuple[int, int]:
    """Two socios totalling exactly 100 via the API (interim update first)."""
    a_id = _crear_socio(client, token, "100")
    _actualizar_socio(client, token, a_id, "60")
    b_id = _crear_socio(client, token, "40")
    return a_id, b_id


def _cleanup_all() -> None:
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# FIN-1: MovimientoFinanciero CRUD
# ---------------------------------------------------------------------------


def test_post_movimiento_requires_auth(client):
    """No token -> 401."""
    resp = client.post("/api/v1/finanzas/movimientos", json=_movimiento_payload())
    assert resp.status_code == 401


def test_post_movimiento_consulta_forbidden(client, consulta_token):
    """consulta is READ-only -> 403 on POST /finanzas/movimientos."""
    resp = client.post(
        "/api/v1/finanzas/movimientos",
        json=_movimiento_payload(),
        headers=_auth(consulta_token),
    )
    assert resp.status_code == 403


def test_post_movimiento_operador_201(client, operador_token):
    """operador CAN create -> 201 with persisted Decimal monto (FIN-1)."""
    resp = client.post(
        "/api/v1/finanzas/movimientos",
        json=_movimiento_payload(tipo="Gasto", monto="123.4500"),
        headers=_auth(operador_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["tipo"] == "Gasto"
    assert Decimal(body["monto"]) == Decimal("123.4500")
    assert body["socio_id"] is None
    _cleanup_all()


def test_post_movimiento_tipo_invalido_422(client, admin_token):
    """tipo not in {Gasto, Inversion, Retiro} -> 422 (FIN-1)."""
    resp = client.post(
        "/api/v1/finanzas/movimientos",
        json=_movimiento_payload(tipo="Prestamo"),
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_get_movimientos_consulta_allowed(client, consulta_token):
    """consulta CAN GET /finanzas/movimientos (audited list, FIN-1)."""
    resp = client.get(
        "/api/v1/finanzas/movimientos", headers=_auth(consulta_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_delete_movimiento_soft_delete(client, admin_token):
    """DELETE soft-deletes (estado 'inactivo') and the row disappears from the
    activo list (FIN-1 soft delete)."""
    created = client.post(
        "/api/v1/finanzas/movimientos",
        json=_movimiento_payload(tipo="Inversion"),
        headers=_auth(admin_token),
    )
    assert created.status_code == 201
    mov_id = created.json()["id"]
    try:
        resp = client.delete(
            f"/api/v1/finanzas/movimientos/{mov_id}", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "inactivo"

        lista = client.get(
            "/api/v1/finanzas/movimientos", headers=_auth(admin_token)
        )
        assert lista.status_code == 200
        assert mov_id not in [m["id"] for m in lista.json()]
    finally:
        _cleanup_all()


def test_delete_movimiento_404(client, admin_token):
    """Unknown movimiento id -> 404."""
    resp = client.delete(
        "/api/v1/finanzas/movimientos/99999999", headers=_auth(admin_token)
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# FIN-1: one-time settlement
# ---------------------------------------------------------------------------


def test_settle_liquidacion_60_40_201_y_replay_409(client, admin_token):
    """Settle 1000 with socios 60/40 -> two Retiro rows (600/400); replaying the
    same liquidacion_id -> 409 with no duplicated payouts (FIN-1 one-time)."""
    a_id, b_id = _crear_socios_60_40(client, admin_token)
    try:
        resp = client.post(
            "/api/v1/finanzas/liquidaciones",
            json={"monto": "1000", "notas": "Utilidades Q1", "liquidacion_id": "LIQ-TEST01"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        movs = resp.json()
        assert len(movs) == 2
        assert all(m["tipo"] == "Retiro" for m in movs)
        assert all(m["estado"] == "activo" for m in movs)
        por_socio = {m["socio_id"]: Decimal(m["monto"]) for m in movs}
        assert por_socio[a_id] == Decimal("600.0000")  # 1000 * 60 / 100
        assert por_socio[b_id] == Decimal("400.0000")  # 1000 * 40 / 100

        replay = client.post(
            "/api/v1/finanzas/liquidaciones",
            json={"monto": "1000", "notas": "replay", "liquidacion_id": "LIQ-TEST01"},
            headers=_auth(admin_token),
        )
        assert replay.status_code == 409
    finally:
        _cleanup_all()


def test_settle_liquidacion_consulta_forbidden(client, consulta_token):
    """consulta -> 403 on settlement (mutation)."""
    resp = client.post(
        "/api/v1/finanzas/liquidaciones",
        json={"monto": "100"},
        headers=_auth(consulta_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# FIN-2: SociosConfiguracion — sum-to-100
# ---------------------------------------------------------------------------


def test_socio_crear_suma_exacta_100_201(client, admin_token):
    """Single socio at 100 -> 201 (boundary exact, FIN-2)."""
    try:
        s_id = _crear_socio(client, admin_token, "100")
        resp = client.get("/api/v1/finanzas/socios", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert s_id in [s["id"] for s in resp.json()]
    finally:
        _cleanup_all()


def test_socio_crear_suma_99_422(client, admin_token):
    """Create leaving global sum at 99 -> 422, no row (boundary, FIN-2)."""
    try:
        a_id = _crear_socio(client, admin_token, "100")
        _actualizar_socio(client, admin_token, a_id, "60")
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={"nombre": f"Socio {_unique()}", "porcentaje_participacion": "39"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_socio_crear_suma_101_422(client, admin_token):
    """Create leaving global sum at 101 -> 422, no row (boundary, FIN-2)."""
    try:
        a_id = _crear_socio(client, admin_token, "100")
        _actualizar_socio(client, admin_token, a_id, "60")
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={"nombre": f"Socio {_unique()}", "porcentaje_participacion": "41"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_socio_actualizar_no_excede_100_pero_permite_interino(client, admin_token):
    """Update pushing the sum above 100 -> 422; interim below-100 update is
    allowed (rebalancing, FIN-2)."""
    try:
        a_id = _crear_socio(client, admin_token, "100")
        _actualizar_socio(client, admin_token, a_id, "60")
        b_id = _crear_socio(client, admin_token, "40")
        resp = client.patch(
            f"/api/v1/finanzas/socios/{b_id}",
            json={"porcentaje_participacion": "41"},  # 60 + 41 = 101
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        resp = client.patch(
            f"/api/v1/finanzas/socios/{b_id}",
            json={"porcentaje_participacion": "30"},  # 60 + 30 = 90 interim
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()["porcentaje_participacion"]) == Decimal("30.0000")
    finally:
        _cleanup_all()


def test_socio_eliminar_bloqueado_con_pagos_409(client, admin_token):
    """Delete blocked with 409 when the socio already has payouts (FIN-2)."""
    a_id, b_id = _crear_socios_60_40(client, admin_token)
    try:
        mov = client.post(
            "/api/v1/finanzas/movimientos",
            json=_movimiento_payload(tipo="Retiro", monto="50", socio_id=a_id),
            headers=_auth(admin_token),
        )
        assert mov.status_code == 201
        resp = client.delete(
            f"/api/v1/finanzas/socios/{a_id}", headers=_auth(admin_token)
        )
        assert resp.status_code == 409
    finally:
        _cleanup_all()
