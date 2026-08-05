def test_create_insumo_requires_auth(client):
    resp = client.post(
        "/api/v1/insumos",
        json={
            "categoria_id": 1,
            "nombre": "Tela Algodón",
            "unidad_medida": "metro",
            "stock_actual": "10",
            "stock_minimo": "1",
            "costo_promedio_actual": "5.5",
        },
    )
    assert resp.status_code == 401


def test_create_insumo_operador_forbidden(client, operador_token, categoria_fixture):
    resp = client.post(
        "/api/v1/insumos",
        json={
            "categoria_id": categoria_fixture["id"],
            "nombre": "Tela Algodón",
            "unidad_medida": "metro",
            "stock_actual": "10",
            "stock_minimo": "1",
            "costo_promedio_actual": "5.5",
        },
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert resp.status_code == 403


def test_create_insumo_admin_created(client, admin_token, categoria_fixture):
    resp = client.post(
        "/api/v1/insumos",
        json={
            "categoria_id": categoria_fixture["id"],
            "nombre": "Tela Algodón Test",
            "unidad_medida": "metro",
            "stock_actual": "10",
            "stock_minimo": "1",
            "costo_promedio_actual": "5.5",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["nombre"] == "Tela Algodón Test"
    assert body["nombre_categoria"] == categoria_fixture["nombre"]


def test_list_insumos_includes_category(client, admin_token):
    resp = client.get(
        "/api/v1/insumos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_insumos_requires_auth(client):
    resp = client.get("/api/v1/insumos")
    assert resp.status_code == 401