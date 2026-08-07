"""Devoluciones API endpoint tests — strict TDD (slice 3, task 3.1).

Drives the devoluciones HTTP surface through the FastAPI TestClient against the
real test PostgreSQL:
- POST /devoluciones full cancel -> 201, Venta anulada, ALL BOM stock restored
  (DEV-1); already-anulada / no-material-PO -> 400.
- POST /devoluciones partial -> 201, only the returned line's BOM restored,
  sale stays 'completada', refund priced at the sale-time snapshot (DEV-2);
  qty > sold -> 422; parcial without items -> 422 (schema shape).
- One return per sale: second POST -> 409 (DEV-3).
- GET /devoluciones audited (admin/operador/consulta), filters venta_id /
  fecha range, pagination, items loaded (DEV-4); 401 without token.
- 401 / 403 role gates on mutations.

Sales are created through the real POST /ventas endpoint so the full stack
(router -> service -> engine) is exercised; setup mirrors test_ventas_api.py
with uuid4-unique names and FK-ordered cleanup.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Cliente,
    Devolucion,
    DetalleVenta,
    Insumo,
    Producto,
    TipoProducto,
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


def _make_linea_insumo(
    producto_id: int, insumo_id: int, cantidad: str = "1"
) -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                cantidad_requerida=Decimal(cantidad),
                porcentaje_desperdicio=Decimal("0"),
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


def _read_stock(insumo_id: int) -> Decimal:
    db = SessionLocal()
    try:
        return db.get(Insumo, insumo_id).stock_actual
    finally:
        db.close()


def _read_venta_estado(venta_id: int) -> str:
    db = SessionLocal()
    try:
        return db.get(Venta, venta_id).estado
    finally:
        db.close()


def _count_devoluciones(venta_id: int) -> int:
    db = SessionLocal()
    try:
        return db.query(Devolucion).filter(Devolucion.venta_id == venta_id).count()
    finally:
        db.close()


def _cleanup_devoluciones(venta_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(Devolucion).filter(
            Devolucion.venta_id.in_(venta_ids)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_ventas_for_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = select(DetalleVenta.venta_id).where(
            DetalleVenta.producto_id == producto_id
        )
        db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _cleanup_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
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
) -> dict:
    return {
        "cliente_id": cliente_id,
        "canal_venta": "web",
        "descuento_porcentaje": "0",
        "detalles": [
            {
                "producto_id": producto_id,
                "variante_id": variante_id,
                "cantidad": cantidad,
                "precio_unitario": precio,
            }
        ],
    }


def _crear_venta(client, token: str, payload: dict) -> dict:
    resp = client.post(
        "/api/v1/ventas",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# AUTH / ROLE GATES
# ---------------------------------------------------------------------------


def test_post_devolucion_requires_auth(client):
    """No token -> 401 (spec: unauth -> 401)."""
    resp = client.post(
        "/api/v1/devoluciones",
        json={"venta_id": 99999999, "tipo": "total"},
    )
    assert resp.status_code == 401


def test_post_devolucion_consulta_forbidden(client, consulta_token):
    """consulta is READ-only -> 403 on POST /devoluciones."""
    resp = client.post(
        "/api/v1/devoluciones",
        json={"venta_id": 99999999, "tipo": "total"},
        headers=_auth(consulta_token),
    )
    assert resp.status_code == 403


def test_get_devoluciones_requires_auth(client):
    """No token -> 401 on GET /devoluciones."""
    resp = client.get("/api/v1/devoluciones")
    assert resp.status_code == 401


def test_get_devoluciones_consulta_allowed(client, consulta_token):
    """consulta CAN GET /devoluciones (audited role, DEV-4)."""
    resp = client.get("/api/v1/devoluciones", headers=_auth(consulta_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# DEV-1: FULL CANCEL
# ---------------------------------------------------------------------------


def test_post_devolucion_total_201_anula_y_restaura_stock(client, operador_token):
    """Cancel-full -> 201, tipo 'total', reembolso = full total, Venta
    'anulada', every consumed insumo restored (DEV-1)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="5", stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    cli_id = _make_cliente()
    try:
        venta = _crear_venta(client, operador_token, _venta_payload(prod_id, cliente_id=cli_id))
        assert _read_stock(ins_id) == Decimal("9")  # sale consumed 1

        resp = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": venta["id"], "tipo": "total", "motivo": "cliente final"},
            headers=_auth(operador_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["tipo"] == "total"
        assert Decimal(body["monto_reembolsado"]) == Decimal("10.0000")
        assert body["venta_id"] == venta["id"]
        assert _read_venta_estado(venta["id"]) == "anulada"
        assert _read_stock(ins_id) == Decimal("10")  # fully restored
    finally:
        _cleanup_devoluciones([venta["id"]])
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_cliente(cli_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_total_venta_ya_anulada_400(client, admin_token):
    """Return on an already-anulada sale -> 400, no double restore (DEV-1)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        venta = _crear_venta(client, admin_token, _venta_payload(prod_id))
        r1 = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": venta["id"], "tipo": "total"},
            headers=_auth(admin_token),
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": venta["id"], "tipo": "total"},
            headers=_auth(admin_token),
        )
        assert r2.status_code == 400
        assert _read_stock(ins_id) == Decimal("10")  # restored exactly once
    finally:
        _cleanup_devoluciones([venta["id"]])
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_total_sin_bom_400(client, admin_token):
    """Sale of a product with no consumable BOM -> 400, sale stays 'completada'
    (no-material-PO, DEV-1)."""
    cat_id = _make_categoria()
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)  # no BOM line
    try:
        venta = _crear_venta(client, admin_token, _venta_payload(prod_id))
        resp = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": venta["id"], "tipo": "total"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
        assert _read_venta_estado(venta["id"]) == "completada"
        assert _count_devoluciones(venta["id"]) == 0
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# DEV-2: PARTIAL RETURN
# ---------------------------------------------------------------------------


def test_post_devolucion_parcial_201_restaura_solo_linea_devuelta(
    client, admin_token
):
    """Partial -> 201, only the returned line's insumo restored, sale stays
    'completada', refund = line subtotal at snapshot price (DEV-2)."""
    cat_id = _make_categoria()
    i1 = _make_insumo(cat_id, stock="10")
    i2 = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    p1 = _make_producto(tipo_id)
    p2 = _make_producto(tipo_id)
    _make_linea_insumo(p1, i1, cantidad="1")
    _make_linea_insumo(p2, i2, cantidad="1")
    try:
        payload = {
            "cliente_id": None,
            "canal_venta": "web",
            "descuento_porcentaje": "0",
            "detalles": [
                {"producto_id": p1, "variante_id": None, "cantidad": "1", "precio_unitario": "10"},
                {"producto_id": p2, "variante_id": None, "cantidad": "1", "precio_unitario": "20"},
            ],
        }
        venta = _crear_venta(client, admin_token, payload)
        assert _read_stock(i1) == Decimal("9")
        assert _read_stock(i2) == Decimal("9")

        resp = client.post(
            "/api/v1/devoluciones",
            json={
                "venta_id": venta["id"],
                "tipo": "parcial",
                "items": [
                    {"producto_id": p1, "variante_id": None, "cantidad": "1", "precio_unitario": "10"}
                ],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["tipo"] == "parcial"
        assert Decimal(body["monto_reembolsado"]) == Decimal("10.0000")
        assert len(body["items"]) == 1
        assert body["items"][0]["producto_id"] == p1
        assert Decimal(body["items"][0]["precio_unitario"]) == Decimal("10.0000")
        assert Decimal(body["items"][0]["subtotal"]) == Decimal("10.0000")
        assert _read_stock(i1) == Decimal("10")  # returned line restored
        assert _read_stock(i2) == Decimal("9")  # untouched
        assert _read_venta_estado(venta["id"]) == "completada"
    finally:
        _cleanup_devoluciones([venta["id"]])
        _cleanup_ventas_for_producto(p1)
        _cleanup_ventas_for_producto(p2)
        _cleanup_producto(p1)
        _cleanup_producto(p2)
        _cleanup_insumo(i1)
        _cleanup_insumo(i2)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_parcial_precio_snapshot_no_el_del_cliente(
    client, admin_token
):
    """Refund uses the sale-time snapshot even when the client sends a
    different price in the payload (DEV-2 snapshot rule)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="20")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        v1 = _crear_venta(client, admin_token, _venta_payload(prod_id, precio="10"))
        # later sale of the same product at a different price
        _crear_venta(client, admin_token, _venta_payload(prod_id, precio="25"))

        resp = client.post(
            "/api/v1/devoluciones",
            json={
                "venta_id": v1["id"],
                "tipo": "parcial",
                "items": [
                    {"producto_id": prod_id, "variante_id": None, "cantidad": "1", "precio_unitario": "999"}
                ],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert Decimal(body["monto_reembolsado"]) == Decimal("10.0000")  # snapshot, NOT 999
        assert Decimal(body["items"][0]["precio_unitario"]) == Decimal("10.0000")
    finally:
        _cleanup_devoluciones([v1["id"]])
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_parcial_cantidad_excede_422(client, admin_token):
    """qty > sold -> 422, nothing persisted, stock untouched (DEV-2)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="5")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        venta = _crear_venta(client, admin_token, _venta_payload(prod_id, cantidad="5"))
        assert _read_stock(ins_id) == Decimal("0")
        resp = client.post(
            "/api/v1/devoluciones",
            json={
                "venta_id": venta["id"],
                "tipo": "parcial",
                "items": [
                    {"producto_id": prod_id, "variante_id": None, "cantidad": "6", "precio_unitario": "10"}
                ],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        assert _count_devoluciones(venta["id"]) == 0
        assert _read_stock(ins_id) == Decimal("0")
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_parcial_sin_items_422(client, admin_token):
    """tipo 'parcial' without items -> 422 (schema shape, DEV-2)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        venta = _crear_venta(client, admin_token, _venta_payload(prod_id))
        resp = client.post(
            "/api/v1/devoluciones",
            json={"venta_id": venta["id"], "tipo": "parcial"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
        assert _count_devoluciones(venta["id"]) == 0
    finally:
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


def test_post_devolucion_tipo_invalido_422(client, admin_token):
    """tipo not in Literal['total','parcial'] -> 422."""
    resp = client.post(
        "/api/v1/devoluciones",
        json={"venta_id": 99999999, "tipo": "cancelar"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DEV-3: ONE RETURN PER SALE
# ---------------------------------------------------------------------------


def test_post_devolucion_doble_409(client, admin_token):
    """Second return for the same sale -> 409, stock restored exactly once
    (DEV-3 single-return invariant)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="10")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        venta = _crear_venta(client, admin_token, _venta_payload(prod_id))
        r1 = client.post(
            "/api/v1/devoluciones",
            json={
                "venta_id": venta["id"],
                "tipo": "parcial",
                "items": [
                    {"producto_id": prod_id, "variante_id": None, "cantidad": "1", "precio_unitario": "10"}
                ],
            },
            headers=_auth(admin_token),
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/api/v1/devoluciones",
            json={
                "venta_id": venta["id"],
                "tipo": "parcial",
                "items": [
                    {"producto_id": prod_id, "variante_id": None, "cantidad": "1", "precio_unitario": "10"}
                ],
            },
            headers=_auth(admin_token),
        )
        assert r2.status_code == 409
        assert _count_devoluciones(venta["id"]) == 1
        assert _read_stock(ins_id) == Decimal("10")  # restored once
    finally:
        _cleanup_devoluciones([venta["id"]])
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# DEV-4: LIST + FILTERS
# ---------------------------------------------------------------------------


def test_get_devoluciones_filtros_y_paginacion(client, admin_token):
    """GET filters by venta_id, paginates, loads items; fecha range excluding
    all returns -> empty (DEV-4)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, stock="30")
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id, cantidad="1")
    try:
        v1 = _crear_venta(client, admin_token, _venta_payload(prod_id, cantidad="1"))
        v2 = _crear_venta(client, admin_token, _venta_payload(prod_id, cantidad="2"))
        for vid in (v1["id"], v2["id"]):
            r = client.post(
                "/api/v1/devoluciones",
                json={
                    "venta_id": vid,
                    "tipo": "parcial",
                    "items": [
                        {"producto_id": prod_id, "variante_id": None, "cantidad": "1", "precio_unitario": "10"}
                    ],
                },
                headers=_auth(admin_token),
            )
            assert r.status_code == 201

        # venta_id filter -> only that sale's return, with its items loaded
        resp = client.get(
            f"/api/v1/devoluciones?venta_id={v2['id']}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["venta_id"] == v2["id"]
        assert len(body[0]["items"]) == 1

        # pagination -> at most 1 row
        resp = client.get(
            "/api/v1/devoluciones?limit=1", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # fecha range excluding both returns -> empty (real filter ran)
        resp = client.get(
            "/api/v1/devoluciones?fecha_desde=2000-01-01&fecha_hasta=2000-01-02",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

        # unknown venta -> empty
        resp = client.get(
            "/api/v1/devoluciones?venta_id=99999999", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        _cleanup_devoluciones([v1["id"], v2["id"]])
        _cleanup_ventas_for_producto(prod_id)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)
