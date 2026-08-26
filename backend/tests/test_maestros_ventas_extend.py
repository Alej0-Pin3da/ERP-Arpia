"""VCP-1/2 RED — canales_venta + metodos_pago extended."""
import uuid


def _uq() -> str:
    return uuid.uuid4().hex[:6]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def test_canal_create_and_filter(client, admin_token):
    payload = {"codigo": f"chn_{_uq()}", "nombre": f"Canal {_uq()}", "tipo": "DIGITAL", "comision_pct": 5.5, "costo_fijo_mensual": 100000, "activo": True}
    r = client.post("/api/v1/maestros/canales-venta", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    # filter by tipo
    r2 = client.get("/api/v1/maestros/canales-venta?tipo=DIGITAL", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == cid for it in r2.json()["items"])
    # Paginated shape
    assert "total" in r2.json() and "items" in r2.json()

    # duplicate nombre -> 409 (codigo unique but nombre can be duplicate? spec says nombre UNIQUE for channel)
    # We test duplicate codigo
    dup = client.post("/api/v1/maestros/canales-venta", json=payload, headers=_auth(admin_token))
    assert dup.status_code == 409, dup.text


def test_canal_invalid_tipo_422(client, admin_token):
    r = client.post("/api/v1/maestros/canales-venta", json={"codigo": f"bad_{_uq()}", "nombre": f"Bad {_uq()}", "tipo": "UNKNOWN"}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text
    # comision >100
    r2 = client.post("/api/v1/maestros/canales-venta", json={"codigo": f"bad2_{_uq()}", "nombre": f"Bad2 {_uq()}", "comision_pct": 150}, headers=_auth(admin_token))
    assert r2.status_code == 422, r2.text


def test_canal_patch_delete(client, admin_token):
    r = client.post("/api/v1/maestros/canales-venta", json={"codigo": f"patch_{_uq()}", "nombre": f"PatchC {_uq()}", "tipo": "FISICO"}, headers=_auth(admin_token))
    cid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/canales-venta/{cid}", json={"comision_pct": 2.0}, headers=_auth(admin_token))
    assert rp.status_code == 200
    assert float(rp.json()["comision_pct"]) == 2.0
    d = client.delete(f"/api/v1/maestros/canales-venta/{cid}", headers=_auth(admin_token))
    assert d.status_code == 204
    assert client.get(f"/api/v1/maestros/canales-venta/{cid}", headers=_auth(admin_token)).status_code == 404


def test_metodo_pago_crud_and_filter(client, admin_token):
    payload = {"codigo": f"pay_{_uq()}", "nombre": f"Nequi {_uq()}", "tipo": "BILLETERA_DIGITAL", "comision_pct": 1.5, "tiempo_acreditacion": "Inmediata", "activo": True}
    r = client.post("/api/v1/maestros/metodos-pago", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    r2 = client.get("/api/v1/maestros/metodos-pago?tipo=BILLETERA_DIGITAL", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == mid for it in r2.json()["items"])
    # duplicate nombre -> 409
    dup = client.post("/api/v1/maestros/metodos-pago", json=payload, headers=_auth(admin_token))
    assert dup.status_code == 409, dup.text


def test_metodo_invalid_tipo_422(client, admin_token):
    r = client.post("/api/v1/maestros/metodos-pago", json={"codigo": f"bad_{_uq()}", "nombre": f"BadM {_uq()}", "tipo": "FAKE"}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_metodo_patch_delete(client, admin_token):
    r = client.post("/api/v1/maestros/metodos-pago", json={"codigo": f"mp_{_uq()}", "nombre": f"MP {_uq()}", "tipo": "TRANSFERENCIA"}, headers=_auth(admin_token))
    mid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/metodos-pago/{mid}", json={"tiempo_acreditacion": "24h"}, headers=_auth(admin_token))
    assert rp.status_code == 200
    d = client.delete(f"/api/v1/maestros/metodos-pago/{mid}", headers=_auth(admin_token))
    assert d.status_code == 204
