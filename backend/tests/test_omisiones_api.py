"""Omisiones API endpoint tests — strict TDD (PR3, task T4).

Drives the /api/v1/omisiones HTTP surface through the FastAPI TestClient
against the real test PostgreSQL:
- GET /omisiones: paginated {items, total} with AND-combined filters
  (fase, nivel, hoja, resuelta, fecha_desde/fecha_hasta, q on mensaje),
  audited roles admin|operador|consulta (D8) — MIG-3.
- PATCH /omisiones/{id}: mark/unmark resuelta; require_admin (D9, spec
  MIG-4); 404 when the row does not exist.

The table is populated by the migration CLI hook (migrate/omisiones.py);
tests seed rows directly via SessionLocal and wipe the table at module
start/end (same contract as test_finanzas_api.py).
"""

from datetime import UTC, datetime

import pytest

from app.db.session import SessionLocal
from app.models import MigracionOmision


@pytest.fixture(autouse=True)
def _omisiones_tabla_limpia():
    """Every test starts with zero Migracion_Omisiones rows so count-based
    assertions never see rows seeded by earlier tests."""
    db = SessionLocal()
    try:
        db.query(MigracionOmision).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _crear_omision(
    db,
    *,
    corrida: str = "corrida-1",
    fase: str = "F1",
    hoja: str = "HojaA",
    fila: int | None = 1,
    celda: str | None = "A1",
    nivel: str = "WARN",
    mensaje: str = "divergencia de prueba",
    resuelta: bool = False,
    creado_en: datetime | None = None,
) -> int:
    omision = MigracionOmision(
        corrida_id=corrida,
        fase=fase,
        hoja=hoja,
        fila=fila,
        celda=celda,
        nivel=nivel,
        mensaje=mensaje,
        resuelta=resuelta,
    )
    if creado_en is not None:
        omision.creado_en = creado_en
    db.add(omision)
    db.commit()
    db.refresh(omision)
    return omision.id


def _sembrar_mezcla() -> None:
    """Rows covering every filter axis (run inside a test, then cleaned by
    the module wipe): 2 WARN in F1/HojaA (one resuelta), 1 ERROR in F2/HojaB."""
    db = SessionLocal()
    try:
        _crear_omision(
            db,
            corrida="mezcla-1",
            fase="F1",
            hoja="HojaA",
            nivel="WARN",
            mensaje="celda con divergencia comun",
            resuelta=False,
        )
        _crear_omision(
            db,
            corrida="mezcla-1",
            fase="F1",
            hoja="HojaA",
            nivel="WARN",
            mensaje="otra divergencia",
            resuelta=True,
        )
        _crear_omision(
            db,
            corrida="mezcla-2",
            fase="F2",
            hoja="HojaB",
            nivel="ERROR",
            mensaje="fila invalida marcada",
            resuelta=False,
            creado_en=datetime(2026, 8, 1, tzinfo=UTC),
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# MIG-3: GET /omisiones — paginated, filtrable, audited
# ---------------------------------------------------------------------------


def test_get_omisiones_requires_auth(client):
    resp = client.get("/api/v1/omisiones")
    assert resp.status_code == 401


def test_get_omisiones_paginado_shape(client, admin_token):
    db = SessionLocal()
    try:
        for i in range(3):
            _crear_omision(
                db, corrida=f"shape-{i}", fase="F1", nivel="WARN", mensaje=f"mensaje {i}"
            )
    finally:
        db.close()

    resp = client.get("/api/v1/omisiones", headers=_auth(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"items", "total"}
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert {
        "id",
        "corrida_id",
        "fase",
        "hoja",
        "fila",
        "celda",
        "nivel",
        "mensaje",
        "resuelta",
        "creado_en",
    } <= set(body["items"][0])


def test_get_omisiones_paginado_respeta_limit_offset(client, admin_token):
    db = SessionLocal()
    try:
        for i in range(5):
            _crear_omision(db, corrida=f"page-{i}", fase="F1", nivel="WARN", mensaje=f"m {i}")
    finally:
        db.close()

    resp = client.get("/api/v1/omisiones?limit=2&offset=0", headers=_auth(admin_token))
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5

    resp2 = client.get("/api/v1/omisiones?limit=2&offset=10", headers=_auth(admin_token))
    assert resp2.json()["items"] == []
    assert resp2.json()["total"] == 5  # out-of-range page: empty items, no 404 (API-1)


def test_get_omisiones_filtros_reducen_items_y_total(client, admin_token):
    _sembrar_mezcla()

    # fase: 2 rows in F1
    resp = client.get("/api/v1/omisiones?fase=F1", headers=_auth(admin_token))
    assert resp.json()["total"] == 2
    assert all(i["fase"] == "F1" for i in resp.json()["items"])

    # nivel: 1 ERROR
    resp = client.get("/api/v1/omisiones?nivel=ERROR", headers=_auth(admin_token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["nivel"] == "ERROR"

    # hoja: 2 rows in HojaA
    resp = client.get("/api/v1/omisiones?hoja=HojaA", headers=_auth(admin_token))
    assert resp.json()["total"] == 2

    # resuelta=false: 2 pending rows (the resuelta one is excluded)
    resp = client.get("/api/v1/omisiones?resuelta=false", headers=_auth(admin_token))
    assert resp.json()["total"] == 2
    assert all(i["resuelta"] is False for i in resp.json()["items"])

    # q on mensaje: only the row containing the token
    resp = client.get("/api/v1/omisiones?q=comun", headers=_auth(admin_token))
    assert resp.json()["total"] == 1
    assert "comun" in resp.json()["items"][0]["mensaje"]

    # combined AND: fase=F1 + q=otra -> exactly the resuelta F1 row
    resp = client.get("/api/v1/omisiones?fase=F1&q=otra", headers=_auth(admin_token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["resuelta"] is True


def test_get_omisiones_filtro_fechas(client, admin_token):
    _sembrar_mezcla()

    # The ERROR row is dated 2026-08-01; the WARN rows get server now().
    resp = client.get(
        "/api/v1/omisiones?fecha_desde=2026-08-01&fecha_hasta=2026-08-01",
        headers=_auth(admin_token),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["nivel"] == "ERROR"

    resp2 = client.get("/api/v1/omisiones?fecha_desde=2026-08-02", headers=_auth(admin_token))
    assert resp2.json()["total"] == 2  # only the two now()-dated WARN rows


def test_get_omisiones_422_nivel_invalido(client, admin_token):
    resp = client.get("/api/v1/omisiones?nivel=INFO", headers=_auth(admin_token))
    assert resp.status_code == 422


def test_get_omisiones_roles_audited(client, operador_token, consulta_token):
    """D8: GET is audited — operador and consulta both read 200."""
    resp_op = client.get("/api/v1/omisiones", headers=_auth(operador_token))
    assert resp_op.status_code == 200
    resp_co = client.get("/api/v1/omisiones", headers=_auth(consulta_token))
    assert resp_co.status_code == 200


# ---------------------------------------------------------------------------
# MIG-4: PATCH /omisiones/{id} — mark resuelta, require_admin, 404
# ---------------------------------------------------------------------------


def test_patch_omision_consulta_forbidden(client, consulta_token):
    resp = client.patch(
        "/api/v1/omisiones/1", json={"resuelta": True}, headers=_auth(consulta_token)
    )
    assert resp.status_code == 403


def test_patch_omision_operador_forbidden(client, operador_token):
    """D9: PATCH is require_admin — operador gets 403 despite GET access."""
    resp = client.patch(
        "/api/v1/omisiones/1", json={"resuelta": True}, headers=_auth(operador_token)
    )
    assert resp.status_code == 403


def test_patch_omision_admin_marca_resuelta(client, admin_token):
    db = SessionLocal()
    try:
        omision_id = _crear_omision(db, corrida="patch-1", nivel="WARN", mensaje="a resolver")
    finally:
        db.close()

    resp = client.patch(
        f"/api/v1/omisiones/{omision_id}", json={"resuelta": True}, headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["resuelta"] is True

    # persisted: the next GET shows resuelta true (MIG-4)
    all_items = client.get("/api/v1/omisiones", headers=_auth(admin_token)).json()["items"]
    row = next(r for r in all_items if r["id"] == omision_id)
    assert row["resuelta"] is True


def test_patch_omision_admin_reabre(client, admin_token):
    db = SessionLocal()
    try:
        omision_id = _crear_omision(
            db, corrida="patch-2", nivel="ERROR", mensaje="reabrir", resuelta=True
        )
    finally:
        db.close()

    resp = client.patch(
        f"/api/v1/omisiones/{omision_id}", json={"resuelta": False}, headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["resuelta"] is False


def test_patch_omision_404_inexistente(client, admin_token):
    resp = client.patch(
        "/api/v1/omisiones/999999", json={"resuelta": True}, headers=_auth(admin_token)
    )
    assert resp.status_code == 404
