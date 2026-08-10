"""Productos master CRUD endpoint tests — strict TDD (slice 1, PR 1).

Exercises the spec scenarios for Tipos_Producto, Productos and nested
Variantes_Producto: CRUD status codes, pagination, FK validation,
duplicate handling and authorization (401/403/404/400/409/422).
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import Producto, TipoProducto, VarianteProducto


def _unique() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# DB helpers (direct model setup + cleanup with unique names)
# ---------------------------------------------------------------------------


def _make_tipo(nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        tipo = TipoProducto(nombre=nombre or f"Tipo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_producto_id: int, nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        producto = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=nombre or f"Producto {_unique()}",
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto.id
    finally:
        db.close()


def _make_variante(producto_id: int, nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        variante = VarianteProducto(
            producto_id=producto_id,
            nombre_variante=nombre or f"Variante {_unique()}",
        )
        db.add(variante)
        db.commit()
        db.refresh(variante)
        return variante.id
    finally:
        db.close()


def _cleanup_variante(variante_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(VarianteProducto).filter(VarianteProducto.id == variante_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id == producto_id
        ).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id.in_(
                db.query(Producto.id).filter(Producto.tipo_producto_id == tipo_id)
            )
        ).delete(synchronize_session=False)
        db.query(Producto).filter(Producto.tipo_producto_id == tipo_id).delete(
            synchronize_session=False
        )
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.commit()
    finally:
        db.close()


def _producto_named_exists(nombre: str) -> bool:
    db = SessionLocal()
    try:
        return (
            db.query(Producto.id).filter(Producto.nombre == nombre).first() is not None
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tipos_Producto
# ---------------------------------------------------------------------------


def test_create_tipo_admin_returns_201(client, admin_token):
    nombre = f"Tipo Nuevo {_unique()}"
    resp = client.post(
        "/api/v1/tipos-producto",
        json={"nombre": nombre},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["nombre"] == nombre
    _cleanup_tipo(body["id"])


def test_create_tipo_duplicate_name_returns_409(client, admin_token):
    nombre = f"Tipo Dup {_unique()}"
    tipo_id = _make_tipo(nombre)
    try:
        resp = client.post(
            "/api/v1/tipos-producto",
            json={"nombre": nombre},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409
    finally:
        _cleanup_tipo(tipo_id)


def test_get_tipo_missing_returns_404(client, admin_token):
    resp = client.get(
        "/api/v1/tipos-producto/99999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_list_tipos_paginated_limit_offset_order_by_id(client, admin_token):
    prefix = f"Tipo Pag {_unique()}"
    tipo_ids = [_make_tipo(nombre=f"{prefix} {i}") for i in range(5)]
    try:
        resp = client.get(
            "/api/v1/tipos-producto",
            params={"q": prefix, "limit": 2, "offset": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"items", "total"}
        rows = body["items"]
        assert len(rows) == 2
        assert body["total"] == 5  # count of the filtered set (q), limit ignored
        ordered_ids = sorted(tipo_ids)
        assert [row["id"] for row in rows] == ordered_ids[2:4]
    finally:
        for tipo_id in tipo_ids:
            _cleanup_tipo(tipo_id)


def test_list_tipos_empty_y_422(client, admin_token):
    """q with no match -> {items: [], total: 0}; invalid typed param -> 422."""
    resp = client.get(
        "/api/v1/tipos-producto",
        params={"q": "zzz_no_existe_999"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}

    resp = client.get(
        "/api/v1/tipos-producto",
        params={"limit": "abc"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


def test_update_tipo_returns_200(client, admin_token):
    tipo_id = _make_tipo()
    try:
        nuevo_nombre = f"Tipo Renombrado {_unique()}"
        resp = client.put(
            f"/api/v1/tipos-producto/{tipo_id}",
            json={"nombre": nuevo_nombre},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == nuevo_nombre
    finally:
        _cleanup_tipo(tipo_id)


def test_delete_tipo_returns_204(client, admin_token):
    tipo_id = _make_tipo()
    resp = client.delete(
        f"/api/v1/tipos-producto/{tipo_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204
    assert (
        client.get(
            f"/api/v1/tipos-producto/{tipo_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 404
    )


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------


def test_create_producto_admin_returns_201_with_defaults(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = None
    try:
        resp = client.post(
            "/api/v1/productos",
            json={
                "tipo_producto_id": tipo_id,
                "nombre": f"Producto Nuevo {_unique()}",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        producto_id = body["id"]
        assert body["tipo_producto_id"] == tipo_id
        assert body["requiere_fabricacion"] is True
        assert Decimal(str(body["costos_operativos_fijos"])) == Decimal("0")
        assert Decimal(str(body["precio_venta_sugerido"])) == Decimal("0")
    finally:
        if producto_id is not None:
            _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_create_producto_invalid_tipo_returns_400(client, admin_token):
    nombre = f"Producto FK {_unique()}"
    resp = client.post(
        "/api/v1/productos",
        json={"tipo_producto_id": 99999999, "nombre": nombre},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
    assert not _producto_named_exists(nombre)


def test_create_producto_negative_costos_returns_422(client, admin_token):
    tipo_id = _make_tipo()
    try:
        resp = client.post(
            "/api/v1/productos",
            json={
                "tipo_producto_id": tipo_id,
                "nombre": f"Producto Neg {_unique()}",
                "costos_operativos_fijos": -1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
        resp = client.post(
            "/api/v1/productos",
            json={
                "tipo_producto_id": tipo_id,
                "nombre": f"Producto Neg {_unique()}",
                "precio_venta_sugerido": -1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
    finally:
        _cleanup_tipo(tipo_id)


def test_get_producto_missing_returns_404(client, admin_token):
    resp = client.get(
        "/api/v1/productos/99999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_update_producto_returns_200(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    try:
        nuevo_nombre = f"Producto Renombrado {_unique()}"
        resp = client.put(
            f"/api/v1/productos/{producto_id}",
            json={"nombre": nuevo_nombre},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == nuevo_nombre
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_delete_producto_returns_204(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    resp = client.delete(
        f"/api/v1/productos/{producto_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204
    assert (
        client.get(
            f"/api/v1/productos/{producto_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 404
    )
    _cleanup_tipo(tipo_id)


def test_list_productos_filter_by_tipo(client, admin_token):
    tipo_a = _make_tipo()
    tipo_b = _make_tipo()
    producto_a = _make_producto(tipo_a)
    _make_producto(tipo_b)
    try:
        resp = client.get(
            f"/api/v1/productos?tipo_producto_id={tipo_a}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        rows = body["items"]
        assert set(body.keys()) == {"items", "total"}
        assert len(rows) >= 1
        assert all(row["tipo_producto_id"] == tipo_a for row in rows)
        assert any(row["id"] == producto_a for row in rows)
    finally:
        _cleanup_tipo(tipo_a)
        _cleanup_tipo(tipo_b)


def test_list_productos_q_y_total_filtrado(client, admin_token):
    """q searches nombre; total == count of the filtered set."""
    prefix = f"Prod Pag {_unique()}"
    tipo_id = _make_tipo()
    p1 = _make_producto(tipo_id, nombre=f"{prefix} Uno")
    p2 = _make_producto(tipo_id, nombre=f"{prefix} Dos")
    try:
        resp = client.get(
            "/api/v1/productos",
            params={"q": prefix},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert {row["id"] for row in body["items"]} == {p1, p2}

        resp = client.get(
            "/api/v1/productos",
            params={"q": f"{prefix} Dos"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["id"] == p2
    finally:
        _cleanup_producto(p1)
        _cleanup_producto(p2)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Variantes_Producto (nested)
# ---------------------------------------------------------------------------


def test_create_variante_returns_201(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    try:
        resp = client.post(
            f"/api/v1/productos/{producto_id}/variantes",
            json={"nombre_variante": f"XL {_unique()}"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] > 0
        assert body["producto_id"] == producto_id
        assert body["precio_venta"] is None
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_create_variante_duplicate_name_returns_409(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id, "XL")
    try:
        resp = client.post(
            f"/api/v1/productos/{producto_id}/variantes",
            json={"nombre_variante": "XL"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409
    finally:
        _cleanup_variante(variante_id)
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_list_variantes_missing_product_returns_404(client, admin_token):
    resp = client.get(
        "/api/v1/productos/99999999/variantes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_delete_variante_missing_returns_404(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    try:
        resp = client.delete(
            f"/api/v1/productos/{producto_id}/variantes/99999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_update_variante_returns_200(client, admin_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    try:
        resp = client.put(
            f"/api/v1/productos/{producto_id}/variantes/{variante_id}",
            json={"nombre_variante": "XXL", "precio_venta": "15.5"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["nombre_variante"] == "XXL"
        assert Decimal(str(body["precio_venta"])) == Decimal("15.5")
    finally:
        _cleanup_variante(variante_id)
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_list_productos_sort_by_tipo_y_nombre(client, admin_token):
    """sort_by accepts joined (tipo) and plain (nombre) columns; unknown keys
    fall back to the id-asc default."""
    prefix = f"Prod Sort {_unique()}"
    tipo_id = _make_tipo()
    p1 = _make_producto(tipo_id, nombre=f"{prefix} Zeta")
    p2 = _make_producto(tipo_id, nombre=f"{prefix} Alfa")
    try:
        resp = client.get(
            "/api/v1/productos",
            params={"q": prefix, "sort_by": "nombre", "order": "asc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert rows[0]["id"] == p2  # "Alfa" < "Zeta"
        assert rows[1]["id"] == p1

        resp = client.get(
            "/api/v1/productos",
            params={"q": prefix, "sort_by": "nombre", "order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        rows = resp.json()["items"]
        assert rows[0]["id"] == p1
        assert rows[1]["id"] == p2

        resp = client.get(
            "/api/v1/productos",
            params={"q": prefix, "sort_by": "tipo", "order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert {r["id"] for r in resp.json()["items"]} == {p1, p2}

        resp = client.get(
            "/api/v1/productos",
            params={"q": prefix, "sort_by": "zzz_inexistente", "order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()["items"]]
        assert ids == sorted(ids)
    finally:
        _cleanup_producto(p1)
        _cleanup_producto(p2)
        _cleanup_tipo(tipo_id)


def test_create_tipo_requires_auth(client):
    resp = client.post("/api/v1/tipos-producto", json={"nombre": "Sin Token"})
    assert resp.status_code == 401


def test_create_producto_requires_auth(client):
    resp = client.post(
        "/api/v1/productos", json={"tipo_producto_id": 1, "nombre": "Sin Token"}
    )
    assert resp.status_code == 401


def test_create_variante_requires_auth(client):
    resp = client.post(
        "/api/v1/productos/1/variantes", json={"nombre_variante": "Sin Token"}
    )
    assert resp.status_code == 401


def test_create_tipo_operador_forbidden(client, operador_token):
    resp = client.post(
        "/api/v1/tipos-producto",
        json={"nombre": f"Tipo Op {_unique()}"},
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert resp.status_code == 403


def test_delete_producto_operador_forbidden(client, operador_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    try:
        resp = client.delete(
            f"/api/v1/productos/{producto_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 403
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_get_productos_consulta_allowed(client, consulta_token):
    resp = client.get(
        "/api/v1/productos",
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}
