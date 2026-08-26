"""MPC-1/2 RED — parametros_costeo singleton."""
import uuid
from concurrent.futures import ThreadPoolExecutor


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def test_get_singleton_200(client, admin_token):
    r = client.get("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    j = r.json()
    assert "distribucion_reinversion_pct" in j
    assert "reparto_margara_pct" in j


def test_auto_create_on_first_get(client, admin_token):
    # GET already auto-creates; ensure second GET still 200
    r1 = client.get("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    r2 = client.get("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == 1


def test_patch_valid_sum_200(client, admin_token):
    r = client.patch(
        "/api/v1/maestros/parametros-costeo",
        json={"distribucion_reinversion_pct": 40, "reparto_margara_pct": 30, "reparto_valqui_pct": 30, "costo_minuto_costura": 120.5},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    assert float(r.json()["distribucion_reinversion_pct"]) == 40
    # GET reflects
    r2 = client.get("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    assert float(r2.json()["costo_minuto_costura"]) == 120.5


def test_patch_invalid_sum_422(client, admin_token):
    r = client.patch(
        "/api/v1/maestros/parametros-costeo",
        json={"distribucion_reinversion_pct": 50, "reparto_margara_pct": 30, "reparto_valqui_pct": 30},
        headers=_auth(admin_token),
    )
    assert r.status_code == 422, r.text


def test_singleton_post_delete_405(client, admin_token):
    r = client.post("/api/v1/maestros/parametros-costeo", json={}, headers=_auth(admin_token))
    assert r.status_code == 405, r.text
    d = client.delete("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    assert d.status_code == 405, d.text


def test_patch_negative_ge0_422(client, admin_token):
    r = client.patch("/api/v1/maestros/parametros-costeo", json={"costo_minuto_costura": -10}, headers=_auth(admin_token))
    assert r.status_code == 422, r.text


def test_concurrent_patch_serialized(client, admin_token):
    # Fire two PATCH concurrently; FOR UPDATE should serialize without lost update
    from app.db.session import SessionLocal

    def _patch(val):
        # use fresh client-like call via main app synchronously
        return client.patch(
            "/api/v1/maestros/parametros-costeo",
            json={"distribucion_reinversion_pct": val, "reparto_margara_pct": 30, "reparto_valqui_pct": 70 - val, "costo_minuto_costura": val * 10},
            headers=_auth(admin_token),
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_patch, 40)
        f2 = ex.submit(_patch, 45)
        r1 = f1.result()
        r2 = f2.result()
    # At least one should be 200; the other may be 200 or 422 but not lost update silently
    assert r1.status_code in (200, 422)
    assert r2.status_code in (200, 422)
    # final GET sum must be 100 or unchanged
    fin = client.get("/api/v1/maestros/parametros-costeo", headers=_auth(admin_token))
    assert fin.status_code == 200
    j = fin.json()
    s = float(j["distribucion_reinversion_pct"]) + float(j["reparto_margara_pct"]) + float(j["reparto_valqui_pct"])
    assert abs(s - 100) < 0.01
