"""Maestros Proveedores RED/GREEN — strict TDD for v4-fase3-maestros MP-1/2/3."""
import uuid
import pytest


def _unique() -> str:
    return uuid.uuid4().hex[:6]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _payload(**over):
    base = {
        "nombre": f"Telas Atenea {_unique()}",
        "categoria": "Telas Principales",
        "ciudad": "Pereira",
        "calificacion": 4.8,
        "tiempo_entrega_dias": 3,
        "email": "proveedor@atenea.co",
        "telefono": "+57 300 000 0001",
        "activo": True,
        "notas": "Proveedor premium",
    }
    base.update(over)
    return base


def test_create_proveedor_201_and_get(client, admin_token):
    resp = client.post("/api/v1/maestros/proveedores", json=_payload(), headers=_auth(admin_token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    pid = data["id"]
    assert data["nombre"].startswith("Telas Atenea")
    # GET by id
    resp2 = client.get(f"/api/v1/maestros/proveedores/{pid}", headers=_auth(admin_token))
    assert resp2.status_code == 200
    assert resp2.json()["nombre"] == data["nombre"]


def test_proveedor_duplicate_409(client, admin_token):
    payload = _payload(nombre="DupProv " + _unique())
    r1 = client.post("/api/v1/maestros/proveedores", json=payload, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/v1/maestros/proveedores", json=payload, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text


def test_proveedor_list_paginated_filters(client, admin_token):
    # create 2 with known categoria
    cat = f"CatProve {_unique()}"
    p1 = _payload(nombre=f"PList1 {_unique()}", categoria=cat, ciudad="Pereira")
    p2 = _payload(nombre=f"PList2 {_unique()}", categoria=cat, ciudad="Bogota")
    client.post("/api/v1/maestros/proveedores", json=p1, headers=_auth(admin_token))
    client.post("/api/v1/maestros/proveedores", json=p2, headers=_auth(admin_token))
    resp = client.get(f"/api/v1/maestros/proveedores?categoria={cat}&limit=2&offset=0", headers=_auth(admin_token))
    assert resp.status_code == 200
    j = resp.json()
    assert "items" in j and "total" in j
    assert j["total"] >= 2
    assert len(j["items"]) <= 2

    # q filter
    resp2 = client.get("/api/v1/maestros/proveedores?q=PList1", headers=_auth(admin_token))
    assert resp2.status_code == 200
    assert any("PList1" in it["nombre"] for it in resp2.json()["items"])


def test_proveedor_validation_422(client, admin_token):
    # calificacion >5
    r = client.post("/api/v1/maestros/proveedores", json=_payload(calificacion=6), headers=_auth(admin_token))
    assert r.status_code == 422, r.text
    # bad email
    r2 = client.post("/api/v1/maestros/proveedores", json=_payload(email="not-an-email"), headers=_auth(admin_token))
    assert r2.status_code == 422, r2.text
    # negative tiempo_entrega
    r3 = client.post("/api/v1/maestros/proveedores", json=_payload(tiempo_entrega_dias=-1), headers=_auth(admin_token))
    assert r3.status_code == 422, r3.text


def test_proveedor_delete_204_404(client, admin_token):
    resp = client.post("/api/v1/maestros/proveedores", json=_payload(), headers=_auth(admin_token))
    pid = resp.json()["id"]
    d1 = client.delete(f"/api/v1/maestros/proveedores/{pid}", headers=_auth(admin_token))
    assert d1.status_code == 204, d1.text
    d2 = client.get(f"/api/v1/maestros/proveedores/{pid}", headers=_auth(admin_token))
    assert d2.status_code == 404


def test_proveedor_patch_partial(client, admin_token):
    resp = client.post("/api/v1/maestros/proveedores", json=_payload(), headers=_auth(admin_token))
    pid = resp.json()["id"]
    r = client.patch(f"/api/v1/maestros/proveedores/{pid}", json={"ciudad": "Manizales", "calificacion": 3.5}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["ciudad"] == "Manizales"
    assert float(r.json()["calificacion"]) == 3.5
