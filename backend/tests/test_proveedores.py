"""Proveedores API endpoint tests — strict TDD.

Covers the proveedores spec: authorization (401/403/201/200), pagination,
server-side sorting (sort_by/order across nombre/ubicacion/contacto) and 404
for missing rows. Exercises the FastAPI routes through the TestClient against
the real test PostgreSQL.
"""

import uuid

from app.db.session import SessionLocal
from app.models import Proveedor

URL = "/api/v1/proveedores"


def _unique() -> str:
    return uuid.uuid4().hex[:12]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_proveedor(nombre: str | None = None, ubicacion: str | None = None) -> int:
    db = SessionLocal()
    try:
        proveedor = Proveedor(
            nombre=nombre or f"Proveedor {_unique()}",
            ubicacion=ubicacion,
        )
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        return proveedor.id
    finally:
        db.close()


def _cleanup_proveedor(proveedor_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(Proveedor).filter(Proveedor.id == proveedor_id).delete()
        db.commit()
    finally:
        db.close()


def _valid_payload(**overrides) -> dict:
    payload = {"nombre": f"Proveedor API {_unique()}"}
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_post_unauth_401(client):
    resp = client.post(URL, json=_valid_payload())
    assert resp.status_code == 401


def test_get_unauth_401(client):
    resp = client.get(URL)
    assert resp.status_code == 401


def test_post_operador_403(client, operador_token):
    resp = client.post(URL, json=_valid_payload(), headers=_auth(operador_token))
    assert resp.status_code == 403


def test_post_admin_201(client, admin_token):
    proveedor_id = None
    try:
        resp = client.post(URL, json=_valid_payload(), headers=_auth(admin_token))
        assert resp.status_code == 201
        body = resp.json()
        proveedor_id = body["id"]
        assert body["id"] > 0
        assert body["nombre"]
    finally:
        if proveedor_id is not None:
            _cleanup_proveedor(proveedor_id)


def test_get_consulta_200(client, consulta_token):
    resp = client.get(URL, headers=_auth(consulta_token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}


# ---------------------------------------------------------------------------
# List: pagination + server-side sorting
# ---------------------------------------------------------------------------


def test_list_paginated_limit_offset(client, admin_token):
    prefix = f"Proveedor Pag {_unique()}"
    ids = [_make_proveedor(nombre=f"{prefix} {i}") for i in range(5)]
    try:
        resp = client.get(
            URL,
            params={"q": prefix, "limit": 2, "offset": 2},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        ordered = sorted(ids)
        assert [row["id"] for row in body["items"]] == ordered[2:4]
    finally:
        for proveedor_id in ids:
            _cleanup_proveedor(proveedor_id)


def test_list_sort_by_ubicacion_nombre_contacto(client, admin_token):
    prefix = f"Prov Sort {_unique()}"
    a = _make_proveedor(nombre=f"{prefix} Zeta", ubicacion="Bogota")
    b = _make_proveedor(nombre=f"{prefix} Alfa", ubicacion="Medellin")
    try:
        resp = client.get(
            URL,
            params={"q": prefix, "sort_by": "nombre", "order": "asc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert [row["id"] for row in rows] == [b, a]

        resp = client.get(
            URL,
            params={"q": prefix, "sort_by": "ubicacion", "order": "desc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert [r["ubicacion"] for r in rows] == ["Medellin", "Bogota"]

        # contacto is nullable -> NULL rows sort first in asc (Postgres); the
        # endpoint just needs to accept the sort key and order.
        resp = client.get(
            URL,
            params={"q": prefix, "sort_by": "contacto", "order": "asc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200

        # Unknown key -> 200, default id-asc preserved.
        resp = client.get(
            URL,
            params={"q": prefix, "sort_by": "zzz_inexistente", "order": "desc"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        ids = [row["id"] for row in resp.json()["items"]]
        assert ids == sorted(ids)
    finally:
        _cleanup_proveedor(a)
        _cleanup_proveedor(b)


# ---------------------------------------------------------------------------
# GET /{id}
# ---------------------------------------------------------------------------


def test_get_missing_404(client, admin_token):
    resp = client.get(f"{URL}/99999999", headers=_auth(admin_token))
    assert resp.status_code == 404