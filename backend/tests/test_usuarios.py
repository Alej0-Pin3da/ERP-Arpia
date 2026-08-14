import uuid


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:8]}@arpia.com"


def _create_user(client, token, role="operador"):
    """Create a user via the API and return the parsed response body."""
    payload = {
        "nombre": "Nuevo Usuario",
        "email": _unique_email("user"),
        "password": "Operador123!",
        "rol": role,
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=_auth(token))
    return resp, payload


def test_admin_creates_operador(client, admin_token):
    resp, payload = _create_user(client, admin_token)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["email"] == payload["email"]
    assert body["rol"] == "operador"
    assert "password" not in body
    assert "password_hash" not in body


def test_create_duplicate_email_400(client, admin_token):
    # First create succeeds, creating the same email again must be rejected.
    resp, payload = _create_user(client, admin_token)
    assert resp.status_code == 201
    dup = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Dup",
            "email": payload["email"],
            "password": "Operador123!",
            "rol": "operador",
        },
        headers=_auth(admin_token),
    )
    assert dup.status_code == 400


def test_operador_cannot_create_user(client, operador_token):
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Blocked",
            "email": _unique_email("blocked"),
            "password": "Operador123!",
            "rol": "operador",
        },
        headers=_auth(operador_token),
    )
    assert resp.status_code == 403


def test_list_usuarios_admin(client, admin_token):
    # Ensure at least one user exists (admin seed + maybe others).
    resp = client.get("/api/v1/usuarios", headers=_auth(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 1
    assert body["total"] >= len(body["items"])
    assert all("password_hash" not in u for u in body["items"])


def test_list_usuarios_filtro_rol_y_q(client, admin_token):
    resp = client.get(
        "/api/v1/usuarios",
        params={"rol": "consulta"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(u["rol"] == "consulta" for u in body["items"])
    assert body["total"] == len(body["items"])  # small page; rol filter ran

    resp = client.get(
        "/api/v1/usuarios",
        params={"q": "zzz_no_existe_999"},
        headers=_auth(admin_token),
    )
    assert resp.json() == {"items": [], "total": 0}

    resp = client.get(
        "/api/v1/usuarios",
        params={"rol": "invalido"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_admin_cannot_delete_self(client, admin_token):
    me = client.get("/api/v1/auth/me", headers=_auth(admin_token)).json()
    resp = client.delete(f"/api/v1/usuarios/{me['id']}", headers=_auth(admin_token))
    assert resp.status_code == 400


def test_patch_password_changes_login(client, admin_token):
    created = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Patch Me",
            "email": _unique_email("patch"),
            "password": "OldPass123!",
            "rol": "operador",
        },
        headers=_auth(admin_token),
    ).json()
    patch = client.patch(
        f"/api/v1/usuarios/{created['id']}",
        json={"password": "NewPass123!"},
        headers=_auth(admin_token),
    )
    assert patch.status_code == 200

    old = client.post(
        "/api/v1/auth/login",
        json={"email": created["email"], "password": "OldPass123!"},
    )
    assert old.status_code == 401

    new = client.post(
        "/api/v1/auth/login",
        json={"email": created["email"], "password": "NewPass123!"},
    )
    assert new.status_code == 200


def test_admin_cannot_demote_self(client, admin_token):
    me = client.get("/api/v1/auth/me", headers=_auth(admin_token)).json()
    resp = client.patch(
        f"/api/v1/usuarios/{me['id']}",
        json={"rol": "operador"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 400
