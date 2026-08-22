def test_login_admin_returns_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@arpia.com", "password": "Admin123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["rol"] == "admin"


def test_login_wrong_password_rejected(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@arpia.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_me_with_token(client, admin_token):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@arpia.com"
    assert body["rol"] == "admin"


def test_me_without_token_rejected(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token_rejected(client):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
