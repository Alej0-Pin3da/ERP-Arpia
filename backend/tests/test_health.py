def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_root_includes_api(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "status" in resp.json()


def test_health_live(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_ready(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}
