"""MT-1 / MPS-1 RED — tallas_estandar + producto_sin_talla."""
import uuid


def _uq() -> str:
    return uuid.uuid4().hex[:6]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


# Tallas estandar

def test_tallas_seed_6_rows(client, admin_token):
    r = client.get("/api/v1/maestros/tallas-estandar?sort_by=orden&order=asc&limit=20", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    # at least 6 seeded XXS..XL
    talla_names = {i["talla"] for i in items}
    for expected in ["XXS", "XS", "S", "M", "L", "XL"]:
        assert expected in talla_names, f"missing {expected} in seed"


def test_create_talla_201_sorted(client, admin_token):
    payload = {"talla": f"XXL_{_uq()}", "orden": 99, "busto": "84 - 88 cm", "cintura": "70 - 74 cm", "cadera": "94 - 98 cm", "reduccion_corset": "-6 cm", "descripcion": "Test XXL"}
    r = client.post("/api/v1/maestros/tallas-estandar", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    # sorted list
    r2 = client.get("/api/v1/maestros/tallas-estandar?sort_by=orden&order=asc&limit=50", headers=_auth(admin_token))
    assert r2.status_code == 200
    ords = [it["orden"] for it in r2.json()["items"]]
    assert ords == sorted(ords), "not sorted by orden"
    assert r2.json()["items"][0]["talla"] == "XXS"


def test_talla_duplicate_409(client, admin_token):
    payload = {"talla": f"DupT_{_uq()}", "orden": 200}
    r1 = client.post("/api/v1/maestros/tallas-estandar", json=payload, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    # duplicate talla
    r2 = client.post("/api/v1/maestros/tallas-estandar", json=payload, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text
    # duplicate orden different talla
    r3 = client.post("/api/v1/maestros/tallas-estandar", json={"talla": f"DupT2_{_uq()}", "orden": 200}, headers=_auth(admin_token))
    assert r3.status_code == 409, r3.text


def test_talla_invalid_422(client, admin_token):
    # missing talla
    r = client.post("/api/v1/maestros/tallas-estandar", json={"orden": 300}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_talla_patch_delete(client, admin_token):
    r = client.post("/api/v1/maestros/tallas-estandar", json={"talla": f"PatchT_{_uq()}", "orden": 250}, headers=_auth(admin_token))
    tid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/tallas-estandar/{tid}", json={"descripcion": "Updated"}, headers=_auth(admin_token))
    assert rp.status_code == 200
    d = client.delete(f"/api/v1/maestros/tallas-estandar/{tid}", headers=_auth(admin_token))
    assert d.status_code == 204
    assert client.get(f"/api/v1/maestros/tallas-estandar/{tid}", headers=_auth(admin_token)).status_code == 404


# Productos sin talla

def test_create_producto_sin_talla_201(client, admin_token):
    payload = {"nombre": f"Tote Bag Atenea {_uq()}", "categoria": "Merch", "precio_sugerido": 45000, "dimensiones": "40x35", "materiales": "Lona"}
    r = client.post("/api/v1/maestros/productos-sin-talla", json=payload, headers=_auth(admin_token))
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    r2 = client.get("/api/v1/maestros/productos-sin-talla?categoria=Merch", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert any(it["id"] == pid for it in r2.json()["items"])


def test_producto_duplicate_409(client, admin_token):
    name = f"DupProd {_uq()}"
    p = {"nombre": name, "categoria": "Merch", "precio_sugerido": 10000}
    r1 = client.post("/api/v1/maestros/productos-sin-talla", json=p, headers=_auth(admin_token))
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/v1/maestros/productos-sin-talla", json=p, headers=_auth(admin_token))
    assert r2.status_code == 409, r2.text


def test_producto_negative_precio_422(client, admin_token):
    r = client.post("/api/v1/maestros/productos-sin-talla", json={"nombre": f"Bad {_uq()}", "categoria": "Merch", "precio_sugerido": -10}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_producto_patch_delete(client, admin_token):
    r = client.post("/api/v1/maestros/productos-sin-talla", json={"nombre": f"PatchP {_uq()}", "categoria": "Merch", "precio_sugerido": 5000}, headers=_auth(admin_token))
    pid = r.json()["id"]
    rp = client.patch(f"/api/v1/maestros/productos-sin-talla/{pid}", json={"precio_sugerido": 6000}, headers=_auth(admin_token))
    assert rp.status_code == 200
    assert float(rp.json()["precio_sugerido"]) == 6000
    d = client.delete(f"/api/v1/maestros/productos-sin-talla/{pid}", headers=_auth(admin_token))
    assert d.status_code == 204
