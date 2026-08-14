"""Ventas API endpoint tests — strict TDD (PR 3 slice, tasks 3.1-3.3 + 4.1-4.2).

Drives the ventas HTTP surface through the FastAPI TestClient against the real
test PostgreSQL:
- POST /ventas happy path 201 with per-line `costo_unitario_aplicado` snapshot
  persisted at engine precision (4-dec).
- 401 unauth, 403 role-restricted (consulta may NOT create; operador MAY),
  404 missing product / cliente, 409 insufficient stock, 400 foreign
  variant, 422 invalid canal / discount / quantity.
- GET /ventas audited (admin/operador/consulta).

Reuses the _unique() uuid4 helper and direct model setup (mirroring
test_inventory.py) to build products, insumos with stock/cost, variants,
BOM lines and clientes; FK-ordered cleanup.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Cliente,
    DetalleVenta,
    Insumo,
    Producto,
    TipoProducto,
    VarianteProducto,
    Venta,
)


def _unique() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# DB helpers (unique names; FK-ordered cleanup)
# ---------------------------------------------------------------------------


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Categoria {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat.id
    finally:
        db.close()


def _make_insumo(categoria_id: int, costo: str = "0", stock: str = "0") -> int:
    db = SessionLocal()
    try:
        ins = Insumo(
            categoria_id=categoria_id,
            nombre=f"Insumo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(costo),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        return ins.id
    finally:
        db.close()


def _make_tipo() -> int:
    db = SessionLocal()
    try:
        tipo = TipoProducto(nombre=f"Tipo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_producto_id: int) -> int:
    db = SessionLocal()
    try:
        prod = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=f"Producto {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return prod.id
    finally:
        db.close()


def _make_variante(producto_id: int) -> int:
    db = SessionLocal()
    try:
        var = VarianteProducto(producto_id=producto_id, nombre_variante=f"Variante {_unique()}")
        db.add(var)
        db.commit()
        db.refresh(var)
        return var.id
    finally:
        db.close()


def _make_linea_insumo(
    producto_id: int,
    insumo_id: int,
    variante_id: int | None = None,
    cantidad: str = "1",
    desperdicio: str = "0",
) -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                variante_id=variante_id,
                cantidad_requerida=Decimal(cantidad),
                porcentaje_desperdicio=Decimal(desperdicio),
            )
        )
        db.commit()
    finally:
        db.close()


def _make_cliente() -> int:
    db = SessionLocal()
    try:
        cli = Cliente(nombre=f"Cliente {_unique()}")
        db.add(cli)
        db.commit()
        db.refresh(cli)
        return cli.id
    finally:
        db.close()


def _cleanup_ventas_for_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = select(DetalleVenta.venta_id).where(DetalleVenta.producto_id == producto_id)
        db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(VarianteProducto).filter(VarianteProducto.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_insumo(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.insumo_id == insumo_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_categoria(categoria_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == categoria_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_cliente(cliente_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(Cliente).filter(Cliente.id == cliente_id).delete()
        db.commit()
    finally:
        db.close()


def _venta_payload(
    producto_id: int,
    cantidad: str = "1",
    precio: str = "10",
    variante_id: int | None = None,
    cliente_id: int | None = None,
    canal: str = "web",
    descuento: str = "0",
) -> dict:
    return {
        "cliente_id": cliente_id,
        "canal_venta": canal,
        "descuento_porcentaje": descuento,
        "detalles": [
            {
                "producto_id": producto_id,
                "variante_id": variante_id,
                "cantidad": cantidad,
                "precio_unitario": precio,
            }
        ],
    }


def _read_stock(insumo_id: int) -> Decimal:
    db = SessionLocal()
    try:
        return db.get(Insumo, insumo_id).stock_actual
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4.1 AUTH / ROLE (RED)
# ---------------------------------------------------------------------------


def test_post_venta_requires_auth(client):
    """No token -> 401 (spec authorization: unauth -> 401)."""
    resp = client.post("/api/v1/ventas", json=_venta_payload(99999999))
    assert resp.status_code == 401


def test_post_venta_consulta_forbidden(client, consulta_token):
    """consulta is READ-only -> 403 on POST /ventas."""
    resp = client.post(
        "/api/v1/ventas",
        json=_venta_payload(99999999),
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 403


def test_get_ventas_consulta_allowed(client, consulta_token):
    """consulta CAN GET /ventas (audited role)."""
    resp = client.get(
        "/api/v1/ventas",
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}


def test_get_ventas_paginado_filtros(client, operador_token):
    """Ventas paginates with limit/offset and filters canal_venta + estado."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        for _ in range(3):
            resp = client.post(
                "/api/v1/ventas",
                json=_venta_payload(prod_id, canal="feria"),
                headers={"Authorization": f"Bearer {operador_token}"},
            )
            assert resp.status_code == 201
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, canal="web"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201

        # limit/offset honored + total = full filtered count
        resp = client.get(
            "/api/v1/ventas",
            params={"canal_venta": "feria", "limit": 2, "offset": 0},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 3
        assert all(v["canal_venta"] == "feria" for v in body["items"])

        # empty filter -> {items: [], total: 0}
        resp = client.get(
            "/api/v1/ventas",
            params={"estado": "anulada"},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"items": [], "total": 0}

        # invalid canal -> 422
        resp = client.get(
            "/api/v1/ventas",
            params={"canal_venta": "tienda"},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 422
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_get_ventas_filtro_producto(client, operador_token):
    """?producto_id=X returns only ventas that include product X in ANY detalle
    (multi-producto ventas match too); ventas without X are excluded."""
    cat_a = _make_categoria()
    cat_b = _make_categoria()
    ins_a = _make_insumo(cat_a, stock="10")
    ins_b = _make_insumo(cat_b, stock="10")
    tipo_id = _make_tipo()
    prod_a = _make_producto(tipo_id)
    prod_b = _make_producto(tipo_id)
    _make_linea_insumo(prod_a, ins_a, cantidad="1")
    _make_linea_insumo(prod_b, ins_b, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_a),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_a = resp.json()["id"]

        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_b),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_b = resp.json()["id"]

        # A sale spanning both products (multi-line detalle).
        resp = client.post(
            "/api/v1/ventas",
            json={
                "cliente_id": None,
                "canal_venta": "web",
                "descuento_porcentaje": "0",
                "detalles": [
                    {
                        "producto_id": prod_a,
                        "variante_id": None,
                        "cantidad": "1",
                        "precio_unitario": "10",
                    },
                    {
                        "producto_id": prod_b,
                        "variante_id": None,
                        "cantidad": "1",
                        "precio_unitario": "10",
                    },
                ],
            },
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_ab = resp.json()["id"]

        # producto_id=prod_a -> venta_a + venta_ab, never venta_b.
        resp = client.get(
            "/api/v1/ventas",
            params={"producto_id": prod_a},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        ids = {v["id"] for v in body["items"]}
        assert ids == {venta_a, venta_ab}
        assert body["total"] == 2

        # producto_id=prod_b -> venta_b + venta_ab, never venta_a.
        resp = client.get(
            "/api/v1/ventas",
            params={"producto_id": prod_b},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        ids = {v["id"] for v in body["items"]}
        assert ids == {venta_b, venta_ab}
        assert body["total"] == 2

        # No filter -> all three.
        resp = client.get(
            "/api/v1/ventas",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 3
    finally:
        _cleanup_ventas_for_producto(prod_a)
        _cleanup_ventas_for_producto(prod_b)
        _cleanup_producto(prod_a)
        _cleanup_producto(prod_b)
        _cleanup_insumo(ins_a)
        _cleanup_insumo(ins_b)
        _cleanup_categoria(cat_a)
        _cleanup_categoria(cat_b)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 4.2 HAPPY PATH + SNAPSHOT (RED -> GREEN)
# ---------------------------------------------------------------------------


def _is_non_decreasing(values) -> bool:
    return all(a <= b for a, b in zip(values, values[1:], strict=False))


def test_list_ventas_sort_server_side(client, operador_token):
    """sort_by/order are honored server-side: total_venta asc is non-decreasing,
    desc non-increasing; unknown sort keys fall back to the id-asc default."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        for cantidad in ("1", "2", "3"):
            resp = client.post(
                "/api/v1/ventas",
                json=_venta_payload(prod_id, cantidad=cantidad),
                headers={"Authorization": f"Bearer {operador_token}"},
            )
            assert resp.status_code == 201

        params = {"sort_by": "total_venta", "order": "asc", "limit": 2000}
        resp = client.get(
            "/api/v1/ventas",
            params=params,
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        asc_totals = [Decimal(v["total_venta"]) for v in resp.json()["items"]]
        assert _is_non_decreasing(asc_totals)

        params["order"] = "desc"
        resp = client.get(
            "/api/v1/ventas",
            params=params,
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        desc_totals = [Decimal(v["total_venta"]) for v in resp.json()["items"]]
        assert _is_non_decreasing(desc_totals[::-1])

        # Unknown sort key -> 200 with default id-asc ordering (whitelist no-op).
        resp = client.get(
            "/api/v1/ventas",
            params={"sort_by": "sql_injection", "order": "desc"},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        ids = [v["id"] for v in resp.json()["items"]]
        assert _is_non_decreasing(ids)
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_venta_operador_201(client, operador_token):
    """operador CAN create (roles admin|operador) -> 201 (triangulation)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="5", stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        assert _read_stock(ins_id) == Decimal("9")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_happy_path_cost_snapshot(client, admin_token):
    """201; `costo_unitario_aplicado` snapshot = 5.1234 (4-dec) persisted at
    engine precision; stock deducted (spec 'cost snapshot persisted')."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="5.1234", stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    cli_id = _make_cliente()
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cliente_id=cli_id),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] > 0
        assert len(body["detalles"]) == 1
        assert Decimal(body["detalles"][0]["costo_unitario_aplicado"]) == Decimal("5.1234")
        assert Decimal(body["detalles"][0]["cantidad"]) == Decimal("1")
        assert Decimal(body["total_venta"]) == Decimal("10.0000")  # 1 x 10
        assert _read_stock(ins_id) == Decimal("9")  # stock actually deducted
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_cliente(cli_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 4.2 ERROR MAPPING (RED -> GREEN)
# ---------------------------------------------------------------------------


def test_create_venta_missing_producto_404(client, admin_token):
    """Nonexistent producto_id -> 404 (spec: missing product)."""
    resp = client.post(
        "/api/v1/ventas",
        json=_venta_payload(99999999),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_create_venta_missing_cliente_404(client, admin_token):
    """Nonexistent cliente_id -> 404 (spec: missing cliente)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cliente_id=99999999),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404
    finally:
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_foreign_variant_400(client, admin_token):
    """variante_id bound to ANOTHER product -> 400, nothing written."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_a = _make_producto(tipo_id)
    prod_b = _make_producto(tipo_id)
    var_b = _make_variante(prod_b)
    _make_linea_insumo(prod_a, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_a, variante_id=var_b),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400
    finally:
        _cleanup_ventas_for_producto(prod_a)
        _cleanup_ventas_for_producto(prod_b)
        _cleanup_producto(prod_a)
        _cleanup_producto(prod_b)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_insufficient_stock_409(client, admin_token):
    """Sell 3 with stock 1 -> 409; nothing writes (all-or-nothing)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="1")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="3"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409
        assert _read_stock(ins_id) == Decimal("1")  # untouched
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_invalid_canal_422(client, admin_token):
    """canal_venta not in the Literal -> 422 (spec: invalid channel)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, canal="tienda"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
    finally:
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_invalid_discount_422(client, admin_token):
    """descuento_porcentaje out of 0..100 -> 422."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, descuento="150"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
    finally:
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_create_venta_invalid_quantity_422(client, admin_token):
    """detalle cantidad 0 -> 422 (Field gt=0)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="0"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
    finally:
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# es_regalo: gift sales (design confirmed 2026-08-12)
# ---------------------------------------------------------------------------


def test_post_venta_normal_total_mayor_cero(client, operador_token):
    """A normal sale (es_regalo=false) keeps its real total > 0."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json={**_venta_payload(prod_id, precio="10"), "es_regalo": False},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["es_regalo"] is False
        assert Decimal(body["total_venta"]) == Decimal("10.0000")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_venta_es_regalo_total_cero_y_stock_descontado(client, operador_token):
    """es_regalo=true -> total_venta is 0 BUT the material explosion still
    deducts stock (the gift still consumes insumos)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json={**_venta_payload(prod_id, precio="10"), "es_regalo": True},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["es_regalo"] is True
        assert Decimal(body["total_venta"]) == Decimal("0.0000")
        assert _read_stock(ins_id) == Decimal("9")  # stock STILL deducted
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_patch_venta_marcar_regalo(client, operador_token):
    """PATCH /ventas/{id} {es_regalo: true} marks the gift flag and returns the
    updated venta; total_venta is NOT touched (historical price kept)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert resp.json()["es_regalo"] is False

        resp = client.patch(
            f"/api/v1/ventas/{venta_id}",
            json={"es_regalo": True},
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == venta_id
        assert body["es_regalo"] is True
        assert Decimal(body["total_venta"]) == Decimal("10.0000")  # unchanged
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_patch_venta_marcar_regalo_404(client, operador_token):
    """PATCH on a nonexistent venta -> 404 "Venta no encontrada"."""
    resp = client.patch(
        "/api/v1/ventas/99999999",
        json={"es_regalo": True},
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Venta no encontrada"


def test_patch_venta_marcar_regalo_consulta_forbidden(client, consulta_token):
    """consulta is read-only -> 403 on PATCH /ventas/{id}."""
    resp = client.patch(
        "/api/v1/ventas/1",
        json={"es_regalo": True},
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /ventas/{id}: edit (recalc total + stock rebalance, ONE atomic commit)
# ---------------------------------------------------------------------------


def test_put_venta_edita_cantidad_recalcula_y_rebalancea_stock(client, operador_token):
    """Edit the quantity of a sale: total recalculated and stock rebalanced.

    BOM: product consumes 10 of insumo X (stock 100).
      - sell 2  -> stock 100 -> 80
      - edit 3  -> restock 20 (-> 100) then deduct 30 -> 70
      - edit 1  -> restock 30 (-> 100) then deduct 10 -> 90
    """
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="10")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="2", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_id) == Decimal("80")

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id, cantidad="3", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["total_venta"]) == Decimal("30.0000")
        assert Decimal(body["detalles"][0]["cantidad"]) == Decimal("3")
        assert _read_stock(ins_id) == Decimal("70")

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id, cantidad="1", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["total_venta"]) == Decimal("10.0000")
        assert Decimal(body["detalles"][0]["cantidad"]) == Decimal("1")
        assert _read_stock(ins_id) == Decimal("90")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_put_venta_cambia_producto_repone_viejo_y_descuenta_nuevo(client, operador_token):
    """Switching the sold product restores the old insumo and deducts the new
    one: prod_a consumes 10 of X (stock 100), prod_b consumes 5 of Y (50)."""
    cat_x = _make_categoria()
    cat_y = _make_categoria()
    ins_x = _make_insumo(cat_x, stock="100")
    ins_y = _make_insumo(cat_y, stock="50")
    tipo_id = _make_tipo()
    prod_a = _make_producto(tipo_id)
    prod_b = _make_producto(tipo_id)
    _make_linea_insumo(prod_a, ins_x, cantidad="10")
    _make_linea_insumo(prod_b, ins_y, cantidad="5")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_a, cantidad="2", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_x) == Decimal("80")
        assert _read_stock(ins_y) == Decimal("50")

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_b, cantidad="3", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["detalles"]) == 1
        assert body["detalles"][0]["producto_id"] == prod_b
        assert Decimal(body["detalles"][0]["cantidad"]) == Decimal("3")
        assert Decimal(body["total_venta"]) == Decimal("30.0000")
        assert _read_stock(ins_x) == Decimal("100")  # old explosion restored
        assert _read_stock(ins_y) == Decimal("35")  # new explosion deducted
    finally:
        _cleanup_ventas_for_producto(prod_a)
        _cleanup_ventas_for_producto(prod_b)
        _cleanup_producto(prod_a)
        _cleanup_producto(prod_b)
        _cleanup_insumo(ins_x)
        _cleanup_insumo(ins_y)
        _cleanup_categoria(cat_x)
        _cleanup_categoria(cat_y)
        _cleanup_tipo(tipo_id)


def test_put_venta_edita_precio_y_cliente(client, operador_token):
    """Editing price/cliente keeps stock untouched but updates total and
    cliente_id (venta_id is immutable)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="10")
    cli_a = _make_cliente()
    cli_b = _make_cliente()
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="2", precio="10", cliente_id=cli_a),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_id) == Decimal("80")

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id, cantidad="2", precio="25", cliente_id=cli_b),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["cliente_id"] == cli_b
        assert Decimal(body["total_venta"]) == Decimal("50.0000")
        assert _read_stock(ins_id) == Decimal("80")  # same explosion, no net move
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)
        _cleanup_cliente(cli_a)
        _cleanup_cliente(cli_b)


def test_put_venta_stock_insuficiente_409_atomico(client, operador_token):
    """Editing to a quantity the available stock cannot cover -> 409 AND the
    old state is fully preserved: the restored stock is rolled back and the
    venta keeps its original lines/total."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="10")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="2", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_id) == Decimal("80")

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id, cantidad="100", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 409

        # Old stock restored AND rolled back -> back to 80; venta untouched.
        assert _read_stock(ins_id) == Decimal("80")
        resp = client.get(
            "/api/v1/ventas",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        venta = next(v for v in resp.json()["items"] if v["id"] == venta_id)
        assert len(venta["detalles"]) == 1
        assert Decimal(venta["detalles"][0]["cantidad"]) == Decimal("2")
        assert Decimal(venta["total_venta"]) == Decimal("20.0000")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_put_venta_anulada_400(client, operador_token):
    """Editing an anulada venta -> 400 (history is immutable)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        resp = client.delete(
            f"/api/v1/ventas/{venta_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200

        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "No se puede editar una venta anulada"
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_put_venta_inexistente_404(client, operador_token):
    """PUT on a nonexistent venta -> 404."""
    resp = client.put(
        "/api/v1/ventas/99999999",
        json=_venta_payload(1),
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Venta 99999999 no encontrado"


def test_put_venta_consulta_forbidden(client, consulta_token):
    """consulta is read-only -> 403 on PUT /ventas/{id}."""
    resp = client.put(
        "/api/v1/ventas/1",
        json=_venta_payload(1),
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /ventas/{id}: anular (soft-cancel, NOT a physical delete)
# ---------------------------------------------------------------------------


def test_delete_venta_anula_y_repone_stock(client, operador_token):
    """DELETE marks estado='anulada' and restores the BOM stock; the row is
    KEPT (soft delete — history preserved)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="10")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="2", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_id) == Decimal("80")

        resp = client.delete(
            f"/api/v1/ventas/{venta_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == venta_id
        assert body["estado"] == "anulada"
        assert _read_stock(ins_id) == Decimal("100")  # fully restored

        # The record still exists (soft delete) and lists as anulada.
        resp = client.get(
            "/api/v1/ventas",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        venta = next(v for v in resp.json()["items"] if v["id"] == venta_id)
        assert venta["estado"] == "anulada"
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_delete_venta_repetido_400(client, operador_token):
    """Anularing an already-anulada venta -> 400 (single anular invariant)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]

        resp = client.delete(
            f"/api/v1/ventas/{venta_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200

        resp = client.delete(
            f"/api/v1/ventas/{venta_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "La venta ya está anulada"
        assert _read_stock(ins_id) == Decimal("10")  # not restored twice
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_delete_venta_inexistente_404(client, operador_token):
    """DELETE on a nonexistent venta -> 404."""
    resp = client.delete(
        "/api/v1/ventas/99999999",
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Venta 99999999 no encontrado"


def test_delete_venta_consulta_forbidden(client, consulta_token):
    """consulta is read-only -> 403 on DELETE /ventas/{id}."""
    resp = client.delete(
        "/api/v1/ventas/1",
        headers={"Authorization": f"Bearer {consulta_token}"},
    )
    assert resp.status_code == 403


def test_post_venta_sigue_funcionando_despues_de_editar_y_anular(client, operador_token):
    """POST regression: a normal sale still works after edit/anular ops ran on
    the same product/insumo."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="100")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="10")
    try:
        # edit path
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="1", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]
        assert _read_stock(ins_id) == Decimal("90")
        resp = client.put(
            f"/api/v1/ventas/{venta_id}",
            json=_venta_payload(prod_id, cantidad="2", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        assert _read_stock(ins_id) == Decimal("80")

        # anular path
        resp = client.delete(
            f"/api/v1/ventas/{venta_id}",
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 200
        assert _read_stock(ins_id) == Decimal("100")

        # fresh POST still works
        resp = client.post(
            "/api/v1/ventas",
            json=_venta_payload(prod_id, cantidad="1", precio="10"),
            headers={"Authorization": f"Bearer {operador_token}"},
        )
        assert resp.status_code == 201
        assert _read_stock(ins_id) == Decimal("90")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)
