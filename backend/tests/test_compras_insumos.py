"""Compras insumos endpoint tests — strict TDD (slice 2).

Covers the compras-insumos spec: authorization (401/403/201/200), validation
errors (404/400/422), pagination with limit/offset, optional insumo_id filter,
ordering by id, and read-shape completeness. Exercises the FastAPI routes
through the TestClient against the real test PostgreSQL.
"""

from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models import CategoriaInsumo, CompraInsumo, Insumo, Proveedor

URL = "/api/v1/compras-insumos"


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def proveedor_fixture():
    db = SessionLocal()
    try:
        proveedor = Proveedor(nombre="Proveedor Compras de Pruebas")
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        yield proveedor.id
    finally:
        db.close()


def _make_insumo(categoria_id: int) -> int:
    db = SessionLocal()
    try:
        insumo = Insumo(
            categoria_id=categoria_id,
            nombre=f"Insumo Compras {id(object())}",
            unidad_medida="metro",
            stock_actual=Decimal("0"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("0"),
        )
        db.add(insumo)
        db.commit()
        db.refresh(insumo)
        return insumo.id
    finally:
        db.close()


def _cleanup_insumo(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _valid_payload(insumo_id: int, **overrides) -> dict:
    payload = {
        "insumo_id": insumo_id,
        "cantidad_comprada": 10,
        "precio_unitario_compra": 9,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Requirement: Authorization for purchase operations
# ---------------------------------------------------------------------------


def test_post_unauth_401(client):
    resp = client.post(URL, json=_valid_payload(1))
    assert resp.status_code == 401


def test_get_unauth_401(client):
    resp = client.get(URL)
    assert resp.status_code == 401


def test_post_consulta_403(client, consulta_token):
    resp = client.post(URL, json=_valid_payload(1), headers=_auth(consulta_token))
    assert resp.status_code == 403


def test_post_operador_201(client, operador_token, categoria_fixture, proveedor_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(
                insumo_id,
                proveedor_id=proveedor_fixture,
                cantidad_comprada=20,
                precio_unitario_compra=7,
            ),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["insumo_id"] == insumo_id
        assert data["proveedor_id"] == proveedor_fixture
        assert Decimal(data["cantidad_comprada"]) == Decimal("20")
        assert Decimal(data["precio_unitario_compra"]) == Decimal("7")
        assert data["fecha_compra"]
    finally:
        _cleanup_insumo(insumo_id)


def test_post_without_proveedor_201(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
        assert resp.json()["proveedor_id"] is None
    finally:
        _cleanup_insumo(insumo_id)


def test_get_consulta_200(client, consulta_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.get(URL, headers=_auth(consulta_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        _cleanup_insumo(insumo_id)


# ---------------------------------------------------------------------------
# Requirement: Register an insumo purchase — validation errors
# ---------------------------------------------------------------------------


def test_create_nonexistent_insumo_404(client, operador_token):
    resp = client.post(
        URL,
        json=_valid_payload(99999999),
        headers=_auth(operador_token),
    )
    assert resp.status_code == 404


def test_invalid_proveedor_400(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id, proveedor_id=99999999),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 400
    finally:
        _cleanup_insumo(insumo_id)


@pytest.mark.parametrize("bad_field,bad_value", [("cantidad_comprada", 0), ("cantidad_comprada", -5)])
def test_invalid_quantity_422(client, operador_token, categoria_fixture, bad_field, bad_value):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id, **{bad_field: bad_value}),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_insumo(insumo_id)


@pytest.mark.parametrize("bad_value", [-1, "-0.01"])
def test_invalid_price_422(client, operador_token, categoria_fixture, bad_value):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id, precio_unitario_compra=bad_value),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup_insumo(insumo_id)


# ---------------------------------------------------------------------------
# Requirement: List purchases with pagination and filter
# ---------------------------------------------------------------------------


def test_list_paginated_limit_offset(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        created_ids = []
        for _ in range(4):
            resp = client.post(
                URL,
                json=_valid_payload(insumo_id),
                headers=_auth(operador_token),
            )
            assert resp.status_code == 201
            created_ids.append(resp.json()["id"])

        resp = client.get(
            URL,
            params={"insumo_id": insumo_id, "limit": 2, "offset": 2},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 2
        assert [row["id"] for row in rows] == created_ids[2:4]
    finally:
        _cleanup_insumo(insumo_id)


def test_list_filter_by_insumo(client, operador_token, categoria_fixture):
    insumo_a = _make_insumo(categoria_fixture["id"])
    insumo_b = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL, json=_valid_payload(insumo_a), headers=_auth(operador_token)
        )
        assert resp.status_code == 201
        resp = client.post(
            URL, json=_valid_payload(insumo_b), headers=_auth(operador_token)
        )
        assert resp.status_code == 201

        resp = client.get(
            URL, params={"insumo_id": insumo_a}, headers=_auth(operador_token)
        )
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["insumo_id"] == insumo_a
        assert rows[0]["id"] == resp.json()[0]["id"]
    finally:
        _cleanup_insumo(insumo_a)
        _cleanup_insumo(insumo_b)


def test_list_ordered_by_id(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        created_ids = []
        for _ in range(3):
            resp = client.post(
                URL,
                json=_valid_payload(insumo_id),
                headers=_auth(operador_token),
            )
            assert resp.status_code == 201
            created_ids.append(resp.json()["id"])

        resp = client.get(
            URL, params={"insumo_id": insumo_id}, headers=_auth(operador_token)
        )
        rows = resp.json()
        assert [row["id"] for row in rows] == sorted(created_ids)
    finally:
        _cleanup_insumo(insumo_id)


# ---------------------------------------------------------------------------
# Requirement: Response shape completeness
# ---------------------------------------------------------------------------


def test_read_shape_completeness(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] > 0
        assert data["insumo_id"] == insumo_id
        assert "proveedor_id" in data
        assert "fecha_compra" in data and data["fecha_compra"]
        assert Decimal(data["cantidad_comprada"]) == Decimal("10")
        assert Decimal(data["precio_unitario_compra"]) == Decimal("9")
    finally:
        _cleanup_insumo(insumo_id)
