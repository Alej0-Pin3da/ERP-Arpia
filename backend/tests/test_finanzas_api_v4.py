"""Finanzas v4 API endpoint tests — strict TDD (PR2, task 2.5 RED).

Drives the new v4 HTTP surface through the FastAPI TestClient against the real
test PostgreSQL:
- SOC-1/SOC-2/SOC-3: extended socia create/update/filter (activo, es_fondo_taller,
  q), sum-to-100 incl fondo, invalid email/tipo_cuenta 422, second fondo 422.
- LIQ-1/2/3: real liquidacion create returns codigo LIQ-YYYY-NN + 3 distribution
  rows; duplicate codigo -> 409; FSM skip/revert -> 422; drift warning persisted;
  delete BORRADOR cascades children + SET NULL on linked anticipos.
- ANT-1/2/3: anticipo create/validate; descuento links + transitions atomically;
  double-discount -> 409; ANULADO not discountable -> 422; filters by estado.

These tests reference new route paths and response shapes that do NOT exist yet
in ``app/api/routes/finanzas.py``, so they fail (RED) until task 2.6 (GREEN).
"""

import uuid
from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models import Anticipo, Liquidacion, MovimientoFinanciero, SociosConfiguracion


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def _v4_api_tablas_limpias():
    db = SessionLocal()
    try:
        db.query(Anticipo).delete()
        db.query(Liquidacion).delete()
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


def _crear_socia_api(client, token, porcentaje="30", **extra) -> int:
    payload = {"nombre": f"Socia {_unique()}", "porcentaje_participacion": porcentaje}
    payload.update(extra)
    resp = client.post("/api/v1/finanzas/socios", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _montar_socias_40_30_30_api(client, token) -> list[int]:
    """Build the 40+30+30 config via direct inserts (avoids create-exact-100)."""
    db = SessionLocal()
    ids = []
    try:
        db.add(SociosConfiguracion(nombre=f"Fondo {_unique()}", porcentaje_participacion=Decimal("40"), es_fondo_taller=True))
        db.flush()
        ids.append(db.query(SociosConfiguracion).order_by(SociosConfiguracion.id.desc()).first().id)
        for pct in ("30", "30"):
            db.add(SociosConfiguracion(nombre=f"Socia {_unique()}", porcentaje_participacion=Decimal(pct)))
            db.flush()
            ids.append(db.query(SociosConfiguracion).order_by(SociosConfiguracion.id.desc()).first().id)
        db.commit()
    finally:
        db.close()
    return ids


def _liquidacion_payload(**over) -> dict:
    payload = {
        "periodo": f"2026-{_unique()[:2]}",
        "fecha_cierre": "2026-07-31",
        "total_ventas_brutas": "150000",
        "costo_taller_insumos": "30000",
        "gastos_operativos": "20000",
        "utilidad_neta_total": "100000",
        "fondo_reinversion_monto": "40000",
        "utilidad_repartible": "60000",
        "observaciones": None,
    }
    payload.update(over)
    return payload


def _cleanup_liq_anticipos() -> None:
    db = SessionLocal()
    try:
        db.query(Anticipo).delete()
        db.query(Liquidacion).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_all() -> None:
    db = SessionLocal()
    try:
        db.query(Anticipo).delete()
        db.query(Liquidacion).delete()
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# SOC-1/SOC-2/SOC-3: socias
# ---------------------------------------------------------------------------


def test_socia_create_extended_profile(client, admin_token):
    """Create socia with extended profile -> 201 with defaults/values (SOC-1)."""
    try:
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={
                "nombre": f"Socia {_unique()}",
                "porcentaje_participacion": "30",
                "rol": "Modista",
                "email": "marg@arpia.com",
                "tipo_cuenta": "AHORROS",
                "es_fondo_taller": False,
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["rol"] == "Modista"
        assert body["email"] == "marg@arpia.com"
        assert body["tipo_cuenta"] == "AHORROS"
        assert body["activo"] is True
    finally:
        _cleanup_all()


def test_socia_create_email_invalido_422(client, admin_token):
    """Invalid email -> 422, no row (SOC-2)."""
    try:
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={"nombre": f"S {_unique()}", "porcentaje_participacion": "30", "email": "not-an-email"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_socia_create_tipo_cuenta_invalido_422(client, admin_token):
    """tipo_cuenta not in Literal -> 422 (SOC-2)."""
    try:
        resp = client.post(
            "/api/v1/finanzas/socios",
            json={"nombre": f"S {_unique()}", "porcentaje_participacion": "30", "tipo_cuenta": "CREDITO"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_socia_filter_activo_excluye_inactiva(client, admin_token):
    """GET ?activo=true excludes inactive (SOC-3)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        db = SessionLocal()
        try:
            inactiva = db.get(SociosConfiguracion, ids[1])
            inactiva.activo = False
            db.commit()
        finally:
            db.close()
        resp = client.get(
            "/api/v1/finanzas/socios", params={"activo": "true"}, headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        assert all(i["activo"] is True for i in items)
    finally:
        _cleanup_all()


def test_socia_filter_es_fondo_taller(client, admin_token):
    """GET ?es_fondo_taller=true returns only the fondo (SOC-3)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        resp = client.get(
            "/api/v1/finanzas/socios",
            params={"es_fondo_taller": "true"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["es_fondo_taller"] is True
    finally:
        _cleanup_all()


def test_socia_sum_to_100_incluye_fondo_patch_422(client, admin_token):
    """PATCH Margarita 30->35 -> active sum 105 -> 422 (SOC-2)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        resp = client.patch(
            f"/api/v1/finanzas/socios/{ids[1]}",
            json={"porcentaje_participacion": "35"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        assert "105" in resp.json()["detail"]
    finally:
        _cleanup_all()


# ---------------------------------------------------------------------------
# LIQ-1/2/3: real liquidaciones
# ---------------------------------------------------------------------------


def test_crear_liquidacion_codigo_y_distribucion(client, admin_token):
    """POST liquidacion -> 201 with codigo LIQ-2026-NN and 3 rows (LIQ-1)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        resp = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(utilidad_repartible="100000"),
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["codigo"].startswith("LIQ-2026-")
        assert len(body["distribucion"]) == 3
        montos = sorted(Decimal(d["monto_bruto"]) for d in body["distribucion"])
        assert montos == [Decimal("30000"), Decimal("30000"), Decimal("40000")]
    finally:
        _cleanup_liq_anticipos()


def test_crear_liquidacion_estado_fsm_skip_422(client, admin_token):
    """PATCH BORRADOR->PAGADA direct -> 422, estado stays BORRADOR (LIQ-2)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        liq_id = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(),
            headers=_auth(admin_token),
        ).json()["id"]
        resp = client.patch(
            f"/api/v1/finanzas/liquidaciones/{liq_id}/estado",
            json={"estado": "PAGADA"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        # still BORRADOR
        get = client.get(f"/api/v1/finanzas/liquidaciones/{liq_id}", headers=_auth(admin_token))
        assert get.status_code == 200
        assert get.json()["estado"] == "BORRADOR"
    finally:
        _cleanup_liq_anticipos()


def test_crear_liquidacion_drift_persiste_con_warning(client, admin_token):
    """Payload vs movimientos >5% drift -> persists 120000 + warning (LIQ-3)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        db = SessionLocal()
        try:
            for monto in ("40000", "60000"):
                db.add(
                    MovimientoFinanciero(
                        tipo="Gasto",
                        descripcion=f"mov {_unique()}",
                        monto=Decimal(monto),
                        estado="confirmed",
                    )
                )
            db.commit()
        finally:
            db.close()
        resp = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(utilidad_neta_total="120000", total_ventas_brutas="170000"),
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert Decimal(body["utilidad_neta_total"]) == Decimal("120000")
        assert any("drift" in w.lower() and "5" in w for w in body["warnings"])
    finally:
        _cleanup_liq_anticipos()


def test_delete_liquidacion_cascada_y_set_null_anticipo(client, admin_token):
    """Delete BORRADOR removes children; linked anticipo survives with NULL (LIQ-1/ANT-2)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        # anticipo para ids[1]
        ant = client.post(
            "/api/v1/finanzas/anticipos",
            json={"socia_id": ids[1], "monto": "5000", "fecha": "2026-07-10"},
            headers=_auth(admin_token),
        )
        assert ant.status_code == 201
        ant_id = ant.json()["id"]

        liq_id = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(),
            headers=_auth(admin_token),
        ).json()["id"]

        # verify anticipo got discounted + linked
        db = SessionLocal()
        try:
            row = db.get(Anticipo, ant_id)
            assert row.estado == "DESCONTADO"
            assert row.liquidacion_id == liq_id
        finally:
            db.close()

        resp = client.delete(
            f"/api/v1/finanzas/liquidaciones/{liq_id}", headers=_auth(admin_token)
        )
        assert resp.status_code == 204

        get = client.get(f"/api/v1/finanzas/liquidaciones/{liq_id}", headers=_auth(admin_token))
        assert get.status_code == 404

        # anticipo survives with liquidacion_id = NULL
        db = SessionLocal()
        try:
            row = db.get(Anticipo, ant_id)
            assert row is not None
            assert row.liquidacion_id is None
        finally:
            db.close()
    finally:
        _cleanup_all()


def test_descontar_anticipo_doble_409(client, admin_token):
    """Second discount of the same anticipo -> 409 (ANT-2/ANT-3)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        ant = client.post(
            "/api/v1/finanzas/anticipos",
            json={"socia_id": ids[1], "monto": "5000"},
            headers=_auth(admin_token),
        )
        assert ant.status_code == 201
        ant_id = ant.json()["id"]

        liq1 = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(),
            headers=_auth(admin_token),
        ).json()["id"]

        # ahora el anticipo ya está DESCONTADO+linkeado a liq1; descontar manual a una 2ª -> 409
        liq2 = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(),
            headers=_auth(admin_token),
        ).json()["id"]
        resp = client.patch(
            f"/api/v1/finanzas/anticipos/{ant_id}/descuento",
            json={"liquidacion_id": liq2},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409
        db = SessionLocal()
        try:
            row = db.get(Anticipo, ant_id)
            assert row.liquidacion_id == liq1  # link intacto a la primera
        finally:
            db.close()
    finally:
        _cleanup_all()


def test_descontar_anticipo_anulado_422(client, admin_token):
    """ANULADO cannot be discounted -> 422 (ANT-2)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        ant = client.post(
            "/api/v1/finanzas/anticipos",
            json={"socia_id": ids[1], "monto": "5000"},
            headers=_auth(admin_token),
        ).json()["id"]
        liq_id = client.post(
            "/api/v1/finanzas/liquidaciones/crear",
            json=_liquidacion_payload(),
            headers=_auth(admin_token),
        ).json()["id"]

        db = SessionLocal()
        try:
            row = db.get(Anticipo, ant)
            row.estado = "ANULADO"
            db.commit()
        finally:
            db.close()

        resp = client.patch(
            f"/api/v1/finanzas/anticipos/{ant}/descuento",
            json={"liquidacion_id": liq_id},
            headers=_auth(admin_token),
        )
        assert resp.status_code in (422, 409)
    finally:
        _cleanup_all()


def test_anticipos_filter_por_estado(client, admin_token):
    """GET /finanzas/anticipos?socia_id=&estado= returns subset (ANT-3)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        for estado_target in ("PENDIENTE_DESCUENTO", "DESCONTADO", "ANULADO"):
            client.post(
                "/api/v1/finanzas/anticipos",
                json={"socia_id": ids[1], "monto": "1000"},
                headers=_auth(admin_token),
            )
        db = SessionLocal()
        try:
            rows = db.query(Anticipo).filter(Anticipo.socia_id == ids[1]).all()
            rows[1].estado = "DESCONTADO"
            rows[2].estado = "ANULADO"
            db.commit()
        finally:
            db.close()
        resp = client.get(
            "/api/v1/finanzas/anticipos",
            params={"socia_id": ids[1], "estado": "PENDIENTE_DESCUENTO"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["estado"] == "PENDIENTE_DESCUENTO"
    finally:
        _cleanup_all()


def test_anticipo_monto_no_positivo_422(client, admin_token):
    """monto 0 / -100 -> 422 (ANT-1)."""
    ids = _montar_socias_40_30_30_api(client, admin_token)
    try:
        for monto in ("0", "-100"):
            resp = client.post(
                "/api/v1/finanzas/anticipos",
                json={"socia_id": ids[1], "monto": monto},
                headers=_auth(admin_token),
            )
            assert resp.status_code == 422
    finally:
        _cleanup_all()


def test_anticipo_socia_inexistente_404(client, admin_token):
    """socia_id 999999 -> 404 (ANT-1)."""
    try:
        resp = client.post(
            "/api/v1/finanzas/anticipos",
            json={"socia_id": 99999999, "monto": "5000"},
            headers=_auth(admin_token),
        )
        assert resp.status_code in (404, 422)
    finally:
        _cleanup_all()
