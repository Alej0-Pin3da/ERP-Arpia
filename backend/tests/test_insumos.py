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


def test_list_insumos_paginated_shape(client, admin_token):
    resp = client.get(
        "/api/v1/insumos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)
    # items may include the seeded/category test data; total must equal the
    # count of the filtered set (limit/offset ignored) and items be <= limit.
    assert len(body["items"]) <= 50
    assert body["total"] >= len(body["items"])


def test_list_insumos_filter_q(client, admin_token):
    resp = client.get(
        "/api/v1/insumos",
        params={"q": "zzz_no_existe_999"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"items": [], "total": 0}


def test_list_insumos_filter_categoria(client, admin_token, categoria_fixture):
    resp = client.get(
        "/api/v1/insumos",
        params={"categoria_id": categoria_fixture["id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(i["categoria_id"] == categoria_fixture["id"] for i in body["items"])


def test_list_insumos_offset_fuera_de_rango_no_404(client, admin_token):
    resp = client.get(
        "/api/v1/insumos",
        params={"offset": 999999, "limit": 50},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] >= 0


def test_list_insumos_tipo_invalido_422(client, admin_token):
    resp = client.get(
        "/api/v1/insumos",
        params={"categoria_id": "abc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


def test_list_insumos_requires_auth(client):
    resp = client.get("/api/v1/insumos")
    assert resp.status_code == 401


def test_list_insumos_sort_by_nombre(client, admin_token, categoria_fixture):
    """Server-side ordering: nombre asc/desc reorders created rows; a joined
    sort key (categoria) also works; unknown keys fall back to id-asc."""
    from decimal import Decimal

    from app.db.session import SessionLocal
    from app.models import Insumo

    prefix = f"Insumo Sort {id(object())}"
    ids = []

    db = SessionLocal()
    try:
        for _idx, nombre in enumerate([f"{prefix} Zeta", f"{prefix} Alfa"]):
            ins = Insumo(
                categoria_id=categoria_fixture["id"],
                nombre=nombre,
                unidad_medida="metro",
                stock_actual=Decimal("0"),
                stock_minimo=Decimal("0"),
                costo_promedio_actual=Decimal("0"),
            )
            db.add(ins)
            db.commit()
            db.refresh(ins)
            ids.append(ins.id)
    finally:
        db.close()

    try:
        resp = client.get(
            "/api/v1/insumos",
            params={"q": prefix, "sort_by": "nombre", "order": "asc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert [i["id"] for i in rows] == [ids[1], ids[0]]  # Alfa then Zeta

        resp = client.get(
            "/api/v1/insumos",
            params={"q": prefix, "sort_by": "nombre", "order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert [i["id"] for i in rows] == [ids[0], ids[1]]

        resp = client.get(
            "/api/v1/insumos",
            params={"q": prefix, "sort_by": "categoria", "order": "asc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert {i["id"] for i in resp.json()["items"]} == set(ids)

        resp = client.get(
            "/api/v1/insumos",
            params={"q": prefix, "sort_by": "zzz_inexistente", "order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        got_ids = [i["id"] for i in resp.json()["items"]]
        assert got_ids == sorted(got_ids)  # default id-asc preserved
    finally:
        db = SessionLocal()
        try:
            db.query(Insumo).filter(Insumo.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
