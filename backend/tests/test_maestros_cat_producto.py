"""Master de categorías + líneas de producto (Ficha dropdowns, 0037)."""
import uuid


def _uq() -> str:
    return uuid.uuid4().hex[:6]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


BASE = "/api/v1/maestros/categorias-producto"


def test_create_catprod_201(client, admin_token):
    payload = {"nombre": f"Cat {_uq()}", "tipo": "CATEGORIA"}
    r = client.post(BASE, json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    r2 = client.get(f"{BASE}?tipo=CATEGORIA", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == cid for it in r2.json()["items"])


def test_catprod_duplicate_409(client, admin_token):
    name = f"DupCatProd {_uq()}"
    p = {"nombre": name, "tipo": "LINEA"}
    r1 = client.post(BASE, json=p, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    r2 = client.post(BASE, json=p, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text


def test_catprod_invalid_tipo_422(client, admin_token):
    r = client.post(BASE, json={"nombre": f"Bad {_uq()}", "tipo": "INVALIDO"}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_catprod_patch_and_delete(client, admin_token):
    r = client.post(BASE, json={"nombre": f"PatchCatProd {_uq()}", "tipo": "CATEGORIA"}, headers=_auth(admin_token))
    cid = r.json()["id"]
    rp = client.patch(f"{BASE}/{cid}", json={"activo": False}, headers=_auth(admin_token))
    assert rp.status_code == 200
    assert rp.json()["activo"] is False
    d = client.delete(f"{BASE}/{cid}", headers=_auth(admin_token))
    assert d.status_code == 204
    assert client.get(f"{BASE}/{cid}", headers=_auth(admin_token)).status_code == 404
