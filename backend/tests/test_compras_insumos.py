"""Compras insumos endpoint tests — strict TDD (slice 2).

Covers the compras-insumos spec: authorization (401/403/201/200), validation
errors (404/400/422), pagination with limit/offset, optional insumo_id filter,
ordering by id, and read-shape completeness. Exercises the FastAPI routes
through the TestClient against the real test PostgreSQL.
"""

import uuid
from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models import CompraInsumo, Insumo

URL = "/api/v1/compras-insumos"


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


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
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())}


def _idem() -> dict:
    return {"Idempotency-Key": str(uuid.uuid4())}


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
    resp = client.post(URL, json=_valid_payload(1), headers=_idem())
    assert resp.status_code == 401


def test_get_unauth_401(client):
    resp = client.get(URL)
    assert resp.status_code == 401


def test_post_consulta_403(client, consulta_token):
    resp = client.post(URL, json=_valid_payload(1), headers=_auth(consulta_token))
    assert resp.status_code == 403


def test_post_operador_201(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(
                insumo_id,
                cantidad_comprada=20,
                precio_unitario_compra=7,
            ),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["insumo_id"] == insumo_id
        assert Decimal(data["cantidad_comprada"]) == Decimal("20")
        assert Decimal(data["precio_unitario_compra"]) == Decimal("7")
        assert data["fecha_compra"]
    finally:
        _cleanup_insumo(insumo_id)


def test_post_basic_201(client, operador_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
    finally:
        _cleanup_insumo(insumo_id)


def test_get_consulta_200(client, consulta_token, categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.get(URL, headers=_auth(consulta_token))
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"items", "total"}
        assert isinstance(body["items"], list)
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


@pytest.mark.parametrize(
    "bad_field,bad_value", [("cantidad_comprada", 0), ("cantidad_comprada", -5)]
)
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
        body = resp.json()
        rows = body["items"]
        assert len(rows) == 2
        assert body["total"] == 4  # count of the filtered set, limit ignored
        # Default ordering is fecha_compra DESC (REQ-CI-003) — newest first
        assert [row["id"] for row in rows] == sorted(created_ids, reverse=True)[2:4]
    finally:
        _cleanup_insumo(insumo_id)


def test_list_filter_by_insumo(client, operador_token, categoria_fixture):
    insumo_a = _make_insumo(categoria_fixture["id"])
    insumo_b = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(URL, json=_valid_payload(insumo_a), headers=_auth(operador_token))
        assert resp.status_code == 201
        resp = client.post(URL, json=_valid_payload(insumo_b), headers=_auth(operador_token))
        assert resp.status_code == 201

        resp = client.get(URL, params={"insumo_id": insumo_a}, headers=_auth(operador_token))
        body = resp.json()
        rows = body["items"]
        assert len(rows) == 1
        assert body["total"] == 1
        assert rows[0]["insumo_id"] == insumo_a
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

        resp = client.get(URL, params={"insumo_id": insumo_id}, headers=_auth(operador_token))
        rows = resp.json()["items"]
        # Default DESC by fecha_compra
        assert [row["id"] for row in rows] == sorted(created_ids, reverse=True)
    finally:
        _cleanup_insumo(insumo_id)


def test_list_empty_y_out_of_range_no_404(client, operador_token):
    """No rows -> {items: [], total: 0}; offset beyond set -> empty, no 404."""
    resp = client.get(
        URL,
        params={"insumo_id": 99999999},
        headers=_auth(operador_token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}

    resp = client.get(
        URL,
        params={"limit": 5, "offset": 999999},
        headers=_auth(operador_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] >= 0


# ---------------------------------------------------------------------------
# Server-side sorting (sort_by/order)
# ---------------------------------------------------------------------------


def test_list_sorted_by_price_desc(client, operador_token, categoria_fixture):
    """sort_by=precio_unitario_compra&order=desc -> non-increasing prices; the
    joined insumo sort key is also accepted."""
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        for precio in ("5", "3", "9"):
            resp = client.post(
                URL,
                json=_valid_payload(insumo_id, precio_unitario_compra=precio),
                headers=_auth(operador_token),
            )
            assert resp.status_code == 201

        resp = client.get(
            URL,
            params={
                "insumo_id": insumo_id,
                "sort_by": "precio_unitario_compra",
                "order": "desc",
            },
            headers=_auth(operador_token),
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert [Decimal(r["precio_unitario_compra"]) for r in rows] == [
            Decimal("9"),
            Decimal("5"),
            Decimal("3"),
        ]

        # Joined-column sort key: insumo (Insumo.nombre).
        resp = client.get(
            URL,
            params={"insumo_id": insumo_id, "sort_by": "insumo", "order": "asc"},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 200
        assert all(r["insumo_id"] == insumo_id for r in resp.json()["items"])

        # Unknown key -> 200, default id-asc preserved.
        resp = client.get(
            URL,
            params={"insumo_id": insumo_id, "sort_by": "x; DROP TABLE", "order": "desc"},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()["items"]]
        assert ids == sorted(ids)
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
        assert "fecha_compra" in data and data["fecha_compra"]
        assert Decimal(data["cantidad_comprada"]) == Decimal("10")
        assert Decimal(data["precio_unitario_compra"]) == Decimal("9")
    finally:
        _cleanup_insumo(insumo_id)


# ---------------------------------------------------------------------------
# Requirement: compras-wac-ux  — TOTAL, factura, Infinity/NaN, FK, DESC, RBAC
# ---------------------------------------------------------------------------


def test_post_total_201_with_factura_and_wac(client, operador_token, categoria_fixture):
    """POST TOTAL qty10 costo_total90 facturaF-001 -> 201 unit9 stock20 cost7.0000
    factura stored."""
    # Seed insumo with 10@5 so WAC 10@5+10@9=7 is verifiable via direct DB read
    from app.models import Insumo as _Insumo

    insumo_id = _make_insumo(categoria_fixture["id"])
    # set stock 10 cost 5 explicitly
    try:
        dbs = SessionLocal()
        try:
            ins = dbs.get(_Insumo, insumo_id)
            assert ins is not None
            ins.stock_actual = Decimal("10")
            ins.costo_promedio_actual = Decimal("5")
            dbs.commit()
        finally:
            dbs.close()
        resp = client.post(
            URL,
            json={
                "insumo_id": insumo_id,
                "cantidad_comprada": 10,
                "modo": "TOTAL",
                "costo_total": 90,
                "factura": "F-001",
            },
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert Decimal(data["precio_unitario_compra"]) == Decimal("9")
        assert Decimal(data["costo_unitario_aplicado"]) == Decimal("7")
        assert data["factura"] == "F-001"
        # Verify stock/cost updated
        dbs2 = SessionLocal()
        try:
            ins2 = dbs2.get(_Insumo, insumo_id)
            assert ins2 is not None
            assert ins2.stock_actual == Decimal("20")
            assert ins2.costo_promedio_actual == Decimal("7")
        finally:
            dbs2.close()
    finally:
        _cleanup_insumo(insumo_id)


def test_post_total_422_no_write_infinity_nan(client, operador_token, categoria_fixture):
    """Infinity/NaN/ qty<=0 -> 422 no write (REQ-WAC-002)."""
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        # Quantity zero -> 422
        resp = client.post(
            URL,
            json=_valid_payload(insumo_id, cantidad_comprada=0),
            headers=_auth(operador_token),
        )
        assert resp.status_code == 422
        # Infinity as string via JSON large number not encodable; use string payload
        # that pydantic parses as Decimal
        # Send 1e999 which Decimal would be Infinity if allowed — pydantic should 422 finite
        resp = client.post(
            URL,
            json={
                "insumo_id": insumo_id,
                "cantidad_comprada": 10,
                "precio_unitario_compra": "Infinity",
            },
            headers=_auth(operador_token),
        )
        assert resp.status_code == 422
        resp = client.post(
            URL,
            json={"insumo_id": insumo_id, "cantidad_comprada": 10, "precio_unitario_compra": "NaN"},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 422
        # Ensure no purchase written
        resp2 = client.get(URL, params={"insumo_id": insumo_id}, headers=_auth(operador_token))
        assert resp2.json()["total"] == 0
    finally:
        _cleanup_insumo(insumo_id)


def test_post_404_insumo_and_400_proveedor(client, operador_token, categoria_fixture):
    """Unknown insumo -> 404; unknown proveedor -> 400 (P1-5: validated
    against maestros_proveedores, FK is the backstop)."""
    resp = client.post(
        URL,
        json=_valid_payload(99999999),
        headers=_auth(operador_token),
    )
    assert resp.status_code == 404
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        resp = client.post(
            URL,
            json={**_valid_payload(insumo_id), "proveedor_id": 999999},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 400, resp.text
        assert "Proveedor" in resp.text
    finally:
        _cleanup_insumo(insumo_id)


def test_post_201_con_proveedor_maestro(
    client, operador_token, admin_token, categoria_fixture
):
    """P1-5: a compra with a real maestros_proveedores id -> 201 (FK holds)."""
    insumo_id = _make_insumo(categoria_fixture["id"])
    prov_id = None
    try:
        resp = client.post(
            "/api/v1/maestros/proveedores",
            json={
                "nombre": f"Prov FK {uuid.uuid4().hex[:8]}",
                "categoria": "Telas",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        prov_id = resp.json()["id"]
        resp = client.post(
            URL,
            json={**_valid_payload(insumo_id), "proveedor_id": prov_id},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["proveedor_id"] == prov_id
    finally:
        _cleanup_insumo(insumo_id)
        if prov_id is not None:
            db = SessionLocal()
            try:
                from app.models import ProveedorMaestro

                db.query(ProveedorMaestro).filter(
                    ProveedorMaestro.id == prov_id
                ).delete()
                db.commit()
            finally:
                db.close()


def test_get_desc_order_and_rbac(client, operador_token, consulta_token, categoria_fixture):
    """GET ?insumo_id ordered fecha_compra DESC; consulta GET200 POST403."""
    insumo_id = _make_insumo(categoria_fixture["id"])
    try:
        # Create two purchases with slight delay to ensure distinct timestamps
        import time

        resp1 = client.post(
            URL,
            json=_valid_payload(insumo_id, precio_unitario_compra=5),
            headers=_auth(operador_token),
        )
        assert resp1.status_code == 201
        time.sleep(0.05)
        resp2 = client.post(
            URL,
            json=_valid_payload(insumo_id, precio_unitario_compra=9),
            headers=_auth(operador_token),
        )
        assert resp2.status_code == 201
        # GET as consulta should be 200 and DESC (newest first)
        resp = client.get(URL, params={"insumo_id": insumo_id}, headers=_auth(consulta_token))
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert len(rows) == 2
        # DESC by fecha_compra: second purchase first
        assert rows[0]["id"] == resp2.json()["id"]
        assert rows[1]["id"] == resp1.json()["id"]
        # consulta POST must be 403
        resp_forbidden = client.post(
            URL, json=_valid_payload(insumo_id), headers=_auth(consulta_token)
        )
        assert resp_forbidden.status_code == 403
    finally:
        _cleanup_insumo(insumo_id)
