"""Cotizaciones API endpoint tests.

Drives the /api/v1/cotizaciones HTTP surface through the FastAPI TestClient
against the real test PostgreSQL:
- POST /cotizaciones: snapshots inputs, server-computes costo_total /
  precio_sugerido / ganancia_neta with the Cotizador math; 201; 401 without
  auth; 422 on unknown cliente_id/producto_id or negative inputs.
- GET /cotizaciones: paginated {items, total} with AND-combined filters
  (cliente_id, producto_id, estado, q on nombre_prenda); audited roles.
- GET /cotizaciones/{id}: one quote; 404 when missing.
- PATCH /cotizaciones/{id}/estado: state machine; operador+admin 200,
  consulta 403; invalid estado 422; 404 when missing.

Tests wipe the table at module start/end (same contract as
test_omisiones_api.py) and compare money with Decimal (psycopg Numerics
serialize without float noise).
"""

from decimal import Decimal

import pytest
from app.db.session import SessionLocal
from app.models import Cotizacion


@pytest.fixture(autouse=True)
def _cotizaciones_tabla_limpia():
    """Every test starts with zero Cotizaciones rows so count-based
    assertions never see rows seeded by earlier tests."""
    db = SessionLocal()
    try:
        db.query(Cotizacion).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _payload(**overrides):
    base = {
        "nombre_prenda": "Bustier prueba",
        "metros_tela": 2,
        "precio_metro_tela": 10000,
        "metros_forro": 1,
        "precio_metro_forro": 5000,
        "costo_avios": 3000,
        "costo_empaque": 2000,
        "tiempo_confeccion_min": 60,
        "tarifa_hora": 12000,
        "costo_cif": 1000,
        "margen_pct": 60,
    }
    base.update(overrides)
    return base


def _crear_cotizacion(client, admin_token, **overrides):
    resp = client.post(
        "/api/v1/cotizaciones", json=_payload(**overrides), headers=_auth(admin_token)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# POST /cotizaciones — snapshot + server math, 201/401/422
# ---------------------------------------------------------------------------


def test_post_cotizacion_requires_auth(client):
    resp = client.post("/api/v1/cotizaciones", json=_payload())
    assert resp.status_code == 401


def test_post_cotizacion_computa_resultados(client, admin_token):
    body = _crear_cotizacion(client, admin_token)
    # costo = 2*10000 + 1*5000 + 3000+2000 + (60/60)*12000 + 1000 = 43000
    # margen 60 -> factor 0.4 -> precio 107500, ganancia 64500
    assert Decimal(str(body["costo_total"])) == Decimal("43000")
    assert Decimal(str(body["precio_sugerido"])) == Decimal("107500")
    assert Decimal(str(body["ganancia_neta"])) == Decimal("64500")
    assert Decimal(str(body["margen_pct"])) == Decimal("60")
    assert body["estado"] == "borrador"
    assert body["codigo"] == f"COT-{body['id']:04d}"
    assert body["nombre_prenda"] == "Bustier prueba"


def test_post_cotizacion_margen_100_duplica_22(client, admin_token):
    body = _crear_cotizacion(client, admin_token, margen_pct=100)
    assert Decimal(str(body["precio_sugerido"])) == Decimal(str(body["costo_total"])) * Decimal(
        "2.2"
    )


def test_post_cotizacion_422_producto_inexistente(client, admin_token):
    resp = client.post(
        "/api/v1/cotizaciones", json=_payload(producto_id=999999), headers=_auth(admin_token)
    )
    assert resp.status_code == 422


def test_post_cotizacion_422_cliente_inexistente(client, admin_token):
    resp = client.post(
        "/api/v1/cotizaciones", json=_payload(cliente_id=999999), headers=_auth(admin_token)
    )
    assert resp.status_code == 422


def test_post_cotizacion_422_margen_negativo(client, admin_token):
    resp = client.post(
        "/api/v1/cotizaciones", json=_payload(margen_pct=-5), headers=_auth(admin_token)
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /cotizaciones — paginated, filtrable, audited
# ---------------------------------------------------------------------------


def test_get_cotizaciones_requires_auth(client):
    resp = client.get("/api/v1/cotizaciones")
    assert resp.status_code == 401


def test_get_cotizaciones_paginado_shape(client, admin_token):
    _crear_cotizacion(client, admin_token, nombre_prenda="Prenda A")
    _crear_cotizacion(client, admin_token, nombre_prenda="Prenda B")
    resp = client.get("/api/v1/cotizaciones", headers=_auth(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"items", "total"}
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_get_cotizaciones_filtros(client, admin_token):
    a = _crear_cotizacion(client, admin_token, nombre_prenda="Bustier rojo")
    _crear_cotizacion(client, admin_token, nombre_prenda="Falda azul")
    client.patch(
        f"/api/v1/cotizaciones/{a['id']}/estado",
        json={"estado": "enviada"},
        headers=_auth(admin_token),
    )

    resp = client.get("/api/v1/cotizaciones?estado=enviada", headers=_auth(admin_token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["nombre_prenda"] == "Bustier rojo"

    resp = client.get("/api/v1/cotizaciones?q=azul", headers=_auth(admin_token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["nombre_prenda"] == "Falda azul"


def test_get_cotizaciones_roles_audited(client, operador_token, consulta_token):
    resp_op = client.get("/api/v1/cotizaciones", headers=_auth(operador_token))
    assert resp_op.status_code == 200
    resp_co = client.get("/api/v1/cotizaciones", headers=_auth(consulta_token))
    assert resp_co.status_code == 200


def test_get_cotizacion_404_inexistente(client, admin_token):
    resp = client.get("/api/v1/cotizaciones/999999", headers=_auth(admin_token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /cotizaciones/{id}/estado — state machine, roles, 404/422
# ---------------------------------------------------------------------------


def test_patch_estado_consulta_forbidden(client, consulta_token, admin_token):
    row = _crear_cotizacion(client, admin_token)
    resp = client.patch(
        f"/api/v1/cotizaciones/{row['id']}/estado",
        json={"estado": "enviada"},
        headers=_auth(consulta_token),
    )
    assert resp.status_code == 403


def test_patch_estado_operador_ok(client, operador_token, admin_token):
    row = _crear_cotizacion(client, admin_token)
    resp = client.patch(
        f"/api/v1/cotizaciones/{row['id']}/estado",
        json={"estado": "aprobada"},
        headers=_auth(operador_token),
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "aprobada"


def test_patch_estado_invalido_422(client, admin_token):
    row = _crear_cotizacion(client, admin_token)
    resp = client.patch(
        f"/api/v1/cotizaciones/{row['id']}/estado",
        json={"estado": "facturada"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_patch_estado_404_inexistente(client, admin_token):
    resp = client.patch(
        "/api/v1/cotizaciones/999999/estado", json={"estado": "enviada"}, headers=_auth(admin_token)
    )
    assert resp.status_code == 404
