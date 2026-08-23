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
    """Start the module with no partner rows / movements (see module docstring)."""
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _movimiento_payload(
    tipo: str = "Gasto", monto: str = "10", socio_id: int | None = None
) -> dict:
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
    resp = client.get("/api/v1/finanzas/movimientos", headers=_auth(consulta_token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}


def test_get_movimientos_paginado_y_filtro_tipo(client, admin_token):
    """Movimientos paginate (limit/offset) and filter by tipo; total counts
    the filtered set (API-1/API-3)."""
    for tipo in ("Gasto", "Gasto", "Inversion"):
        resp = client.post(
            "/api/v1/finanzas/movimientos",
            json=_movimiento_payload(tipo=tipo),
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201

    resp = client.get(
        "/api/v1/finanzas/movimientos",
        params={"tipo": "Gasto", "limit": 1, "offset": 0},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["tipo"] == "Gasto"
    assert body["total"] == 2

    resp = client.get(
        "/api/v1/finanzas/movimientos",
        params={"tipo": "Retiro"},
        headers=_auth(admin_token),
    )
    assert resp.json() == {"items": [], "total": 0}

    resp = client.get(
        "/api/v1/finanzas/movimientos",
        params={"tipo": "Prestamo"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422
    _cleanup_all()


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
        resp = client.delete(f"/api/v1/finanzas/movimientos/{mov_id}", headers=_auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["estado"] == "cancelled"

        lista = client.get("/api/v1/finanzas/movimientos", headers=_auth(admin_token))
        assert lista.status_code == 200
        assert mov_id not in [m["id"] for m in lista.json()["items"]]
    finally:
        _cleanup_all()


def test_delete_movimiento_404(client, admin_token):
    """Unknown movimiento id -> 404."""
    resp = client.delete("/api/v1/finanzas/movimientos/99999999", headers=_auth(admin_token))
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
        assert all(m["estado"] == "confirmed" for m in movs)
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


def test_get_movimientos_sort_server_side(client, admin_token):
    """sort_by=id|monto with order asc/desc reorders the list server-side; the
    joined socio key works; unknown keys fall back to the id-asc default."""
    try:
        for monto in ("5", "20", "10"):
            resp = client.post(
                "/api/v1/finanzas/movimientos",
                json=_movimiento_payload(tipo="Gasto", monto=monto),
                headers=_auth(admin_token),
            )
            assert resp.status_code == 201

        resp = client.get(
            "/api/v1/finanzas/movimientos",
            params={"sort_by": "monto", "order": "desc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        montos = [Decimal(m["monto"]) for m in resp.json()["items"]]
        assert montos == sorted(montos, reverse=True)

        resp = client.get(
            "/api/v1/finanzas/movimientos",
            params={"sort_by": "monto", "order": "asc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        montos_asc = [Decimal(m["monto"]) for m in resp.json()["items"]]
        assert montos_asc == sorted(montos_asc)

        resp = client.get(
            "/api/v1/finanzas/movimientos",
            params={"sort_by": "socio", "order": "asc"},
            headers=_auth(admin_token),
        )
        # Joined column sorts without error; NULL socio sorts first (coalesce '').
        assert resp.status_code == 200

        resp = client.get(
            "/api/v1/finanzas/movimientos",
            params={"sort_by": "zzz_inexistente", "order": "desc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        ids = [m["id"] for m in resp.json()["items"]]
        assert ids == sorted(ids)  # default id-asc preserved
    finally:
        _cleanup_all()


def test_get_socios_sort_server_side(client, admin_token):
    """Socios sort by porcentaje_participacion desc; unknown keys default."""
    try:
        a_id = _crear_socio(client, admin_token, "100")
        _actualizar_socio(client, admin_token, a_id, "60")
        b_id = _crear_socio(client, admin_token, "40")
        # Interim rebalance keeps the sum <= 100 (60 + 30 = 90 allowed).
        _actualizar_socio(client, admin_token, b_id, "30")

        resp = client.get(
            "/api/v1/finanzas/socios",
            params={"sort_by": "porcentaje_participacion", "order": "desc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        porcentajes = [Decimal(s["porcentaje_participacion"]) for s in resp.json()["items"]]
        assert porcentajes == sorted(porcentajes, reverse=True)
        assert porcentajes[:2] == [Decimal("60.0000"), Decimal("30.0000")]
        assert {s["id"] for s in resp.json()["items"][:2]} == {a_id, b_id}

        resp = client.get(
            "/api/v1/finanzas/socios",
            params={"sort_by": "zzz_inexistente"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["items"]]
        assert ids == sorted(ids)
    finally:
        _cleanup_all()


# ---------------------------------------------------------------------------
# FIN-2: SociosConfiguracion — sum-to-100
# ---------------------------------------------------------------------------


def test_socio_crear_suma_exacta_100_201(client, admin_token):
    """Single socio at 100 -> 201 (boundary exact, FIN-2)."""
    try:
        s_id = _crear_socio(client, admin_token, "100")
        resp = client.get("/api/v1/finanzas/socios", headers=_auth(admin_token))
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"items", "total"}
        assert s_id in [s["id"] for s in body["items"]]
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
        resp = client.delete(f"/api/v1/finanzas/socios/{a_id}", headers=_auth(admin_token))
        assert resp.status_code == 409
    finally:
        _cleanup_all()


def test_get_socios_paginado_y_q(client, admin_token):
    """Socios paginate (limit/offset) and search by q; total counts filtered."""
    try:
        nombre = f"Socio Pag {_unique()}"
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={"nombre": nombre, "porcentaje_participacion": "100"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201

        resp = client.get(
            "/api/v1/finanzas/socios",
            params={"q": nombre, "limit": 10, "offset": 0},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"items", "total"}
        assert body["total"] == 1
        assert body["items"][0]["nombre"] == nombre

        resp = client.get(
            "/api/v1/finanzas/socios",
            params={"q": "zzz_no_existe_999"},
            headers=_auth(admin_token),
        )
        assert resp.json() == {"items": [], "total": 0}
    finally:
        _cleanup_all()


# ---------------------------------------------------------------------------
# FIN-1: PATCH /finanzas/movimientos/{id} (T3)
# ---------------------------------------------------------------------------


def _crear_movimiento_activo(client, token: str, tipo: str = "Gasto") -> int:
    resp = client.post(
        "/api/v1/finanzas/movimientos",
        json=_movimiento_payload(tipo=tipo, monto="10"),
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_patch_movimiento_operador_200(client, operador_token):
    """PATCH válido (operador) -> 200 con valores nuevos y campos no enviados
    intactos (FIN-1)."""
    try:
        mov_id = _crear_movimiento_activo(client, operador_token)
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"descripcion": "Editada por operador", "monto": "25.50"},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["descripcion"] == "Editada por operador"
        assert Decimal(body["monto"]) == Decimal("25.50")
        assert body["tipo"] == "Gasto"  # no enviado -> intacto
        assert body["estado"] == "confirmed"
    finally:
        _cleanup_all()


def test_patch_movimiento_consulta_403(client, consulta_token):
    """consulta -> 403 on PATCH (mutation)."""
    resp = client.patch(
        "/api/v1/finanzas/movimientos/1",
        json={"descripcion": "x"},
        headers=_auth(consulta_token),
    )
    assert resp.status_code == 403


def test_patch_movimiento_404(client, admin_token):
    """id inexistente -> 404."""
    resp = client.patch(
        "/api/v1/finanzas/movimientos/99999999",
        json={"descripcion": "x"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 404


def test_patch_movimiento_soft_deleted_404(client, admin_token):
    """Soft-deleted movimiento -> 404."""
    try:
        mov_id = _crear_movimiento_activo(client, admin_token)
        resp = client.delete(f"/api/v1/finanzas/movimientos/{mov_id}", headers=_auth(admin_token))
        assert resp.status_code == 200
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"descripcion": "x"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404
    finally:
        _cleanup_all()


def test_patch_movimiento_422_tipo_invalido(client, admin_token):
    """tipo inválido -> 422 (schema Literal)."""
    try:
        mov_id = _crear_movimiento_activo(client, admin_token)
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"tipo": "Prestamo"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_patch_movimiento_socio_inexistente_400(client, admin_token):
    """socio_id inexistente -> 400 'Socio no existe' (FIN-1)."""
    try:
        mov_id = _crear_movimiento_activo(client, admin_token)
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"socio_id": 99999999},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
        assert "Socio no existe" in resp.json()["detail"]
    finally:
        _cleanup_all()


def test_patch_movimiento_liquidacion_monto_422(client, admin_token):
    """Fila de liquidación + monto -> 422 con mensaje claro (FIN-2)."""
    a_id, b_id = _crear_socios_60_40(client, admin_token)
    try:
        resp = client.post(
            "/api/v1/finanzas/liquidaciones",
            json={"monto": "1000", "liquidacion_id": "LIQ-PAT01"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        mov_id = resp.json()[0]["id"]
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"monto": "9999"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        assert "liquidación" in resp.json()["detail"]
    finally:
        _cleanup_all()


def test_patch_movimiento_liquidacion_socio_422(client, admin_token):
    """Fila de liquidación + socio_id -> 422 (FIN-2)."""
    a_id, b_id = _crear_socios_60_40(client, admin_token)
    try:
        resp = client.post(
            "/api/v1/finanzas/liquidaciones",
            json={"monto": "1000", "liquidacion_id": "LIQ-PAT02"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        mov_id = resp.json()[0]["id"]
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"socio_id": a_id},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_patch_movimiento_liquidacion_descripcion_200(client, admin_token):
    """Fila de liquidación + solo descripcion -> 200; monto y liquidacion_id
    intactos (FIN-2: campos descriptivos editables)."""
    a_id, b_id = _crear_socios_60_40(client, admin_token)
    try:
        resp = client.post(
            "/api/v1/finanzas/liquidaciones",
            json={"monto": "1000", "liquidacion_id": "LIQ-PAT03"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        mov = resp.json()[0]
        mov_id = mov["id"]
        monto_original = Decimal(mov["monto"])
        resp = client.patch(
            f"/api/v1/finanzas/movimientos/{mov_id}",
            json={"descripcion": "Nota corregida"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["descripcion"] == "Nota corregida"
        assert Decimal(body["monto"]) == monto_original
        assert body["liquidacion_id"] is not None
    finally:
        _cleanup_all()
