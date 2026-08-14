def test_login_returns_refresh_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "operador@arpia.com", "password": "Operador123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["rol"] == "operador"


def test_refresh_rotates_token(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@arpia.com", "password": "Admin123!"},
    ).json()
    old = login["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"] != old

    # The rotated token works and returns a fresh access token.
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200


def test_refresh_reuse_rejected(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@arpia.com", "password": "Admin123!"},
    ).json()
    old = login["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert first.status_code == 200

    # Reusing the already-rotated token signals compromise.
    second = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert second.status_code == 401


def test_logout_revokes_and_refresh_rejected(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@arpia.com", "password": "Admin123!"},
    ).json()
    token = login["refresh_token"]

    out = client.post("/api/v1/auth/logout", json={"refresh_token": token})
    assert out.status_code == 204

    # Logout is idempotent: repeating it still returns 204.
    again = client.post("/api/v1/auth/logout", json={"refresh_token": token})
    assert again.status_code == 204

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert refresh.status_code == 401


def test_refresh_unknown_token_rejected(client):
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-real-token-value"},
    )
    assert resp.status_code == 401
