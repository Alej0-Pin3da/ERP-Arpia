"""MCU-1/2 RED — categorias coleccion + ubicaciones taller."""
import uuid


def _uq() -> str:
    return uuid.uuid4().hex[:6]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def test_create_categoria_201(client, admin_token):
    payload = {"nombre": f"Atenea Rollos {_uq()}", "tipo_talla": "CON_TALLAS_ESTANDAR", "margen_meta_pct": 35, "descripcion": "Coleccion premium"}
    r = client.post("/api/v1/maestros/categorias-coleccion", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    # filter by tipo_talla
    r2 = client.get("/api/v1/maestros/categorias-coleccion?tipo_talla=CON_TALLAS_ESTANDAR", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == cid for it in r2.json()["items"])


def test_categoria_duplicate_409(client, admin_token):
    name = f"DupCat {_uq()}"
    p = {"nombre": name, "tipo_talla": "TALLA_UNICA"}
    r1 = client.post("/api/v1/maestros/categorias-coleccion", json=p, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/v1/maestros/categorias-coleccion", json=p, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text


def test_categoria_invalid_tipo_422(client, admin_token):
    r = client.post("/api/v1/maestros/categorias-coleccion", json={"nombre": f"Bad {_uq()}", "tipo_talla": "INVALID"}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_categoria_list_paginated_q(client, admin_token):
    name = f"QCat {_uq()}"
    client.post("/api/v1/maestros/categorias-coleccion", json={"nombre": name, "tipo_talla": "SIN_TALLA_MERCH"}, headers=_auth(admin_token))
    r = client.get(f"/api/v1/maestros/categorias-coleccion?q={name[:6]}&limit=1&offset=0", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert len(r.json()["items"]) <= 1


def test_categoria_patch_and_delete(client, admin_token):
    r = client.post("/api/v1/maestros/categorias-coleccion", json={"nombre": f"PatchCat {_uq()}", "tipo_talla": "TALLA_UNICA"}, headers=_auth(admin_token))
    cid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/categorias-coleccion/{cid}", json={"margen_meta_pct": 50}, headers=_auth(admin_token))
    assert rp.status_code == 200
    assert float(rp.json()["margen_meta_pct"]) == 50
    d = client.delete(f"/api/v1/maestros/categorias-coleccion/{cid}", headers=_auth(admin_token))
    assert d.status_code == 204
    assert client.get(f"/api/v1/maestros/categorias-coleccion/{cid}", headers=_auth(admin_token)).status_code == 404


# Ubicaciones

def test_create_ubicacion_201(client, admin_token):
    payload = {"codigo": f"UB-{_uq().upper()}", "nombre": f"Estante Atenea {_uq()}", "tipo": "ROLLOS_TELAS", "capacidad": "25 Rollos"}
    r = client.post("/api/v1/maestros/ubicaciones-taller", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    uid = r.json()["id"]
    r2 = client.get("/api/v1/maestros/ubicaciones-taller?tipo=ROLLOS_TELAS", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == uid for it in r2.json()["items"])


def test_ubicacion_duplicate_codigo_409(client, admin_token):
    code = f"UB-{_uq().upper()}"
    p = {"codigo": code, "nombre": f"U Dup {_uq()}", "tipo": "GAVETAS_HERRAJES"}
    r1 = client.post("/api/v1/maestros/ubicaciones-taller", json=p, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    # duplicate codigo different nombre
    p2 = {"codigo": code, "nombre": f"U Dup2 {_uq()}", "tipo": "GAVETAS_HERRAJES"}
    r2 = client.post("/api/v1/maestros/ubicaciones-taller", json=p2, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text


def test_ubicacion_invalid_tipo_422(client, admin_token):
    r = client.post("/api/v1/maestros/ubicaciones-taller", json={"codigo": f"UB-{_uq().upper()}", "nombre": f"BadU {_uq()}", "tipo": "UNKNOWN"}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_ubicacion_patch_delete(client, admin_token):
    r = client.post("/api/v1/maestros/ubicaciones-taller", json={"codigo": f"UB-{_uq().upper()}", "nombre": f"PatchU {_uq()}", "tipo": "ACCESORIOS_BODEGA"}, headers=_auth(admin_token))
    uid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/ubicaciones-taller/{uid}", json={"capacidad": "50 Prendas"}, headers=_auth(admin_token))
    assert rp.status_code == 200
    assert rp.json()["capacidad"] == "50 Prendas"
    d = client.delete(f"/api/v1/maestros/ubicaciones-taller/{uid}", headers=_auth(admin_token))
    assert d.status_code == 204
    assert client.get(f"/api/v1/maestros/ubicaciones-taller/{uid}", headers=_auth(admin_token)).status_code == 404
