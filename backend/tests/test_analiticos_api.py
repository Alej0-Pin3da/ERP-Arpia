"""Analiticos API endpoint tests — strict TDD (slice 3, tasks 3.1 + 3.4;
ANA-4..6 as the Análisis screen).

Drives the read-only analytics endpoints through the FastAPI TestClient
against the real test PostgreSQL:
- GET /analiticos/ventas-mensuales: GROUP BY month, SUM(total_venta) + count,
  EXCLUDING anulada sales (ANA-1).
- GET /analiticos/insumos-bajo-stock: only insumos with stock_actual <
  stock_minimo, with their minima (ANA-2).
- GET /analiticos/margen-por-producto: margin from the
  Detalle_Ventas.costo_unitario_aplicado SNAPSHOT (never the current WAC),
  excluding anulada lines (ANA-3).
- GET /analiticos/top-productos: SUM(cantidad) + ingresos per product, ordered
  by unidades desc, excluding anulada lines (ANA-4).
- GET /analiticos/top-insumos: SUM(cantidad_comprada) per insumo from
  Compras_Insumos, ordered desc (ANA-5).
- GET /analiticos/finanzas-mensuales: ingresos (non-anulada ventas) vs
  gastos (ACTIVE Gasto|Inversion movimientos) per month, zero-filled (ANA-6).

All are read-only and audited: 401 without token, 200 for admin / operador /
consulta. Sales are inserted directly with explicit `fecha` values so the
monthly grouping and anulada-exclusion are deterministic; the current WAC is
set to a value DIFFERENT from every snapshot to prove the snapshot-only rule.
FK-ordered cleanup.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    CompraInsumo,
    DetalleVenta,
    Insumo,
    MovimientoFinanciero,
    Producto,
    TipoProducto,
    Venta,
)


def _unique() -> str:
    return uuid.uuid4().hex[:12]


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


def _make_insumo(
    categoria_id: int, stock: str = "0", stock_minimo: str = "0", costo: str = "0"
) -> int:
    db = SessionLocal()
    try:
        ins = Insumo(
            categoria_id=categoria_id,
            nombre=f"Insumo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock),
            stock_minimo=Decimal(stock_minimo),
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


def _make_linea_insumo(producto_id: int, insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                cantidad_requerida=Decimal("1"),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
    finally:
        db.close()


def _insertar_venta(
    producto_id: int,
    fecha: datetime,
    total: str,
    estado: str = "completada",
    precio: str = "0",
    costo: str = "0",
    cantidad: str = "1",
) -> int:
    """Insert a Venta + one DetalleVenta directly with a fixed fecha."""
    db = SessionLocal()
    try:
        venta = Venta(
            fecha=fecha,
            canal_venta="web",
            descuento_porcentaje=Decimal("0"),
            estado=estado,
            total_venta=Decimal(total),
        )
        db.add(venta)
        db.flush()
        db.add(
            DetalleVenta(
                venta_id=venta.id,
                producto_id=producto_id,
                variante_id=None,
                cantidad=Decimal(cantidad),
                precio_unitario_aplicado=Decimal(precio),
                costo_unitario_aplicado=Decimal(costo),
            )
        )
        db.commit()
        return venta.id
    finally:
        db.close()


def _insertar_compra(insumo_id: int, cantidad: str) -> int:
    """Insert one CompraInsumo record directly."""
    db = SessionLocal()
    try:
        compra = CompraInsumo(
            insumo_id=insumo_id,
            proveedor_id=None,
            cantidad_comprada=Decimal(cantidad),
            precio_unitario_compra=Decimal("10"),
        )
        db.add(compra)
        db.commit()
        db.refresh(compra)
        return compra.id
    finally:
        db.close()


def _insertar_movimiento(
    fecha: datetime,
    tipo: str,
    monto: str,
    estado: str = "activo",
) -> int:
    """Insert a MovimientoFinanciero directly with a fixed fecha."""
    db = SessionLocal()
    try:
        mov = MovimientoFinanciero(
            fecha=fecha,
            tipo=tipo,
            descripcion=f"Movimiento {tipo}",
            monto=Decimal(monto),
            estado=estado,
        )
        db.add(mov)
        db.commit()
        db.refresh(mov)
        return mov.id
    finally:
        db.close()


def _cleanup_ventas(venta_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(DetalleVenta).filter(
            DetalleVenta.venta_id.in_(venta_ids)
        ).delete(synchronize_session=False)
        db.query(Venta).filter(Venta.id.in_(venta_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _cleanup_compras(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo_id).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _cleanup_movimientos(movimiento_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).filter(
            MovimientoFinanciero.id.in_(movimiento_ids)
        ).delete(synchronize_session=False)
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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# ANA-1: monthly sales (exclude anuladas)
# ---------------------------------------------------------------------------


def test_ventas_mensuales_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/ventas-mensuales")
    assert resp.status_code == 401


def test_ventas_mensuales_consulta_allowed(client, consulta_token):
    """consulta CAN GET (audited role, ANA-1)."""
    resp = client.get(
        "/api/v1/analiticos/ventas-mensuales", headers=_auth(consulta_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_ventas_mensuales_excluye_anuladas(client, admin_token):
    """Two months: 2026-01 has 2 completada (100+200), 2026-02 has 1 completada
    (50) + 1 anulada (9999) -> totals/counts only include non-anulada rows
    (ANA-1)."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="999", stock="0")  # current WAC 999
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id)
    try:
        v_ids = [
            _insertar_venta(prod_id, datetime(2026, 1, 15, 12, 0, 0), "100", precio="100", costo="60"),
            _insertar_venta(prod_id, datetime(2026, 1, 20, 12, 0, 0), "200", precio="100", costo="70"),
            _insertar_venta(prod_id, datetime(2026, 2, 5, 12, 0, 0), "50", precio="100", costo="50"),
            _insertar_venta(prod_id, datetime(2026, 2, 10, 12, 0, 0), "9999", estado="anulada", precio="100", costo="10"),
        ]
        resp = client.get(
            "/api/v1/analiticos/ventas-mensuales", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        por_mes = {r["mes"]: r for r in resp.json()}

        enero = por_mes["2026-01-01"]
        assert Decimal(enero["total"]) == Decimal("300.0000")  # 100 + 200
        assert enero["cantidad"] == 2

        febrero = por_mes["2026-02-01"]
        assert Decimal(febrero["total"]) == Decimal("50.0000")  # anulada 9999 EXCLUDED
        assert febrero["cantidad"] == 1
    finally:
        _cleanup_ventas(v_ids)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# ANA-2: low-stock insumos
# ---------------------------------------------------------------------------


def test_insumos_bajo_stock_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/insumos-bajo-stock")
    assert resp.status_code == 401


def test_insumos_bajo_stock_operador_allowed(client, operador_token):
    """operador CAN GET (audited role, ANA-2)."""
    resp = client.get(
        "/api/v1/analiticos/insumos-bajo-stock", headers=_auth(operador_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_insumos_bajo_stock_solo_bajo_minimo(client, admin_token):
    """Only insumos with stock_actual < stock_minimo are returned, with their
    minima (ANA-2)."""
    cat_id = _make_categoria()
    bajo_a = _make_insumo(cat_id, stock="5", stock_minimo="10")   # below
    sano_b = _make_insumo(cat_id, stock="15", stock_minimo="10")  # above
    bajo_c = _make_insumo(cat_id, stock="0", stock_minimo="5")    # below
    try:
        resp = client.get(
            "/api/v1/analiticos/insumos-bajo-stock", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        body = resp.json()
        por_id = {r["insumo_id"]: r for r in body}

        assert bajo_a in por_id
        assert por_id[bajo_a]["stock_actual"] == "5.0000"
        assert por_id[bajo_a]["stock_minimo"] == "10.0000"

        assert bajo_c in por_id
        assert por_id[bajo_c]["stock_actual"] == "0.0000"
        assert por_id[bajo_c]["stock_minimo"] == "5.0000"

        assert sano_b not in por_id  # above minimum excluded
    finally:
        _cleanup_insumo(bajo_a)
        _cleanup_insumo(sano_b)
        _cleanup_insumo(bajo_c)
        _cleanup_categoria(cat_id)


# ---------------------------------------------------------------------------
# ANA-3: margin per product (snapshot, never current WAC)
# ---------------------------------------------------------------------------


def test_margen_por_producto_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/margen-por-producto")
    assert resp.status_code == 401


def test_margen_por_producto_consulta_allowed(client, consulta_token):
    """consulta CAN GET (audited role, ANA-3)."""
    resp = client.get(
        "/api/v1/analiticos/margen-por-producto", headers=_auth(consulta_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_margen_por_producto_usa_snapshot_y_excluye_anuladas(client, admin_token):
    """Margin uses the Detalle_Ventas.costo_unitario_aplicado snapshot (current
    WAC 999 is IGNORED) and excludes anulada lines (ANA-3).

    Completada lines: (100-60)+(100-70)+(100-50) = 120 total, avg 40.
    Anulada line (100-10=90) must NOT be included.
    """
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="999", stock="0")  # current WAC != snapshot
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id)
    try:
        v_ids = [
            _insertar_venta(prod_id, datetime(2026, 1, 15, 12, 0, 0), "100", precio="100", costo="60"),
            _insertar_venta(prod_id, datetime(2026, 1, 20, 12, 0, 0), "200", precio="100", costo="70"),
            _insertar_venta(prod_id, datetime(2026, 2, 5, 12, 0, 0), "50", precio="100", costo="50"),
            _insertar_venta(prod_id, datetime(2026, 2, 10, 12, 0, 0), "9999", estado="anulada", precio="100", costo="10"),
        ]
        resp = client.get(
            "/api/v1/analiticos/margen-por-producto", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        body = resp.json()
        por_producto = {r["producto_id"]: r for r in body}

        margen = por_producto[prod_id]
        assert Decimal(margen["margen_total"]) == Decimal("120.0000")  # 40+30+50
        assert Decimal(margen["margen_promedio"]) == Decimal("40.0000")
        assert margen["variante_id"] is None
    finally:
        _cleanup_ventas(v_ids)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# ANA-4: top products by units sold (exclude anuladas)
# ---------------------------------------------------------------------------


def test_top_productos_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/top-productos")
    assert resp.status_code == 401


def test_top_productos_consulta_allowed(client, consulta_token):
    """consulta CAN GET (audited role, ANA-4)."""
    resp = client.get(
        "/api/v1/analiticos/top-productos", headers=_auth(consulta_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_top_productos_agrupa_por_producto_y_descarta_anuladas(client, admin_token):
    """Unidades = SUM(cantidad) and ingresos = SUM(cantidad *
    precio_unitario_aplicado) per product, ordered desc by unidades; anulada
    lines are EXCLUDED (ANA-4).

    Producto A: 2+3 unidades (precio 100) -> unidades 5, ingresos 500; plus an
    anulada of 8 unidades -> ignored. Producto B: 1 unidad (precio 150) ->
    unidades 1, ingresos 150.
    """
    tipo_id = _make_tipo()
    prod_a = _make_producto(tipo_id)
    prod_b = _make_producto(tipo_id)
    try:
        v_ids = [
            _insertar_venta(prod_a, datetime(2026, 3, 3, 12, 0, 0), "200", precio="100", cantidad="2"),
            _insertar_venta(prod_a, datetime(2026, 3, 5, 12, 0, 0), "300", precio="100", cantidad="3"),
            _insertar_venta(prod_a, datetime(2026, 3, 9, 12, 0, 0), "9999", estado="anulada", precio="100", cantidad="8"),
            _insertar_venta(prod_b, datetime(2026, 3, 15, 12, 0, 0), "150", precio="150", cantidad="1"),
        ]
        resp = client.get(
            "/api/v1/analiticos/top-productos", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        body = resp.json()
        por_producto = {r["producto_id"]: r for r in body}

        a = por_producto[prod_a]
        assert Decimal(a["unidades"]) == Decimal("5.0000")  # 2 + 3 (anulada 8 EXCLUDED)
        assert Decimal(a["ingresos"]) == Decimal("500.0000")  # 200 + 300

        b = por_producto[prod_b]
        assert Decimal(b["unidades"]) == Decimal("1.0000")
        assert Decimal(b["ingresos"]) == Decimal("150.0000")

        # Ordered by unidades desc: A (5) before B (1).
        indices = [r["producto_id"] for r in body]
        assert indices.index(prod_a) < indices.index(prod_b)
    finally:
        _cleanup_ventas(v_ids)
        _cleanup_producto(prod_a)
        _cleanup_producto(prod_b)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# ANA-5: insumos by purchased quantity
# ---------------------------------------------------------------------------


def test_top_insumos_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/top-insumos")
    assert resp.status_code == 401


def test_top_insumos_operador_allowed(client, operador_token):
    """operador CAN GET (audited role, ANA-5)."""
    resp = client.get(
        "/api/v1/analiticos/top-insumos", headers=_auth(operador_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_top_insumos_suma_compras_y_ordena_desc(client, admin_token):
    """cantidad = SUM(cantidad_comprada) per insumo from Compras_Insumos,
    ordered desc, with the joined name + unit of measure (ANA-5).

    Insumo X: 3 + 2 -> 5. Insumo Y: 4. X (5) must sort before Y (4).
    """
    cat_id = _make_categoria()
    ins_x = _make_insumo(cat_id)
    ins_y = _make_insumo(cat_id)
    try:
        _insertar_compra(ins_x, "3")
        _insertar_compra(ins_x, "2")
        _insertar_compra(ins_y, "4")

        resp = client.get(
            "/api/v1/analiticos/top-insumos", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        body = resp.json()
        por_insumo = {r["insumo_id"]: r for r in body}

        x = por_insumo[ins_x]
        assert Decimal(x["cantidad"]) == Decimal("5.0000")  # 3 + 2
        assert x["unidad_medida"] == "metro"
        assert isinstance(x["nombre"], str) and x["nombre"] != ""

        y = por_insumo[ins_y]
        assert Decimal(y["cantidad"]) == Decimal("4.0000")
        assert y["unidad_medida"] == "metro"

        # Ordered desc by cantidad: X (5) before Y (4).
        indices = [r["insumo_id"] for r in body]
        assert indices.index(ins_x) < indices.index(ins_y)
    finally:
        _cleanup_compras(ins_x)
        _cleanup_compras(ins_y)
        _cleanup_insumo(ins_x)
        _cleanup_insumo(ins_y)
        _cleanup_categoria(cat_id)


# ---------------------------------------------------------------------------
# ANA-6: monthly finanzas trend (ingresos vs gastos)
# ---------------------------------------------------------------------------


def test_finanzas_mensuales_requires_auth(client):
    """No token -> 401."""
    resp = client.get("/api/v1/analiticos/finanzas-mensuales")
    assert resp.status_code == 401


def test_finanzas_mensuales_consulta_allowed(client, consulta_token):
    """consulta CAN GET (audited role, ANA-6)."""
    resp = client.get(
        "/api/v1/analiticos/finanzas-mensuales", headers=_auth(consulta_token)
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_finanzas_mensuales_mezcla_ingresos_y_gastos(client, admin_token):
    """Per month: ingresos = SUM(non-anulada total_venta), gastos = SUM(monto)
    of ACTIVE Gasto|Inversion movements only — Retiros and soft-deleted
    (estado != activo) rows are EXCLUDED; a month with only one side is
    zero-filled on the other (ANA-6).

    2026-04: ventas 100+200 -> ingresos 300; Gasto 80 + Inversion 20 -> 100
      (Gasto 999 inactivo and Retiro 999 both EXCLUDED).
    2026-05: ventas 50 + anulada 9999 -> ingresos 50; no movements -> gastos 0.
    2026-06: no sales -> ingresos 0; Gasto 30 -> gastos 30.
    """
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id)
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id)
    try:
        v_ids = [
            _insertar_venta(prod_id, datetime(2026, 4, 5, 12, 0, 0), "100", precio="100", costo="60"),
            _insertar_venta(prod_id, datetime(2026, 4, 20, 12, 0, 0), "200", precio="100", costo="70"),
            _insertar_venta(prod_id, datetime(2026, 5, 10, 12, 0, 0), "50", precio="100", costo="50"),
            _insertar_venta(prod_id, datetime(2026, 5, 12, 12, 0, 0), "9999", estado="anulada", precio="100", costo="10"),
        ]
        mov_ids = [
            _insertar_movimiento(datetime(2026, 4, 2, 12, 0, 0), "Gasto", "80"),
            _insertar_movimiento(datetime(2026, 4, 3, 12, 0, 0), "Inversion", "20"),
            _insertar_movimiento(datetime(2026, 4, 4, 12, 0, 0), "Gasto", "999", estado="inactivo"),
            _insertar_movimiento(datetime(2026, 4, 6, 12, 0, 0), "Retiro", "999"),
            _insertar_movimiento(datetime(2026, 6, 8, 12, 0, 0), "Gasto", "30"),
        ]
        resp = client.get(
            "/api/v1/analiticos/finanzas-mensuales", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        por_mes = {r["mes"]: r for r in resp.json()}

        abril = por_mes["2026-04-01"]
        assert Decimal(abril["ingresos"]) == Decimal("300.0000")  # 100 + 200
        assert Decimal(abril["gastos"]) == Decimal("100.0000")  # 80 + 20 (inactivo + Retiro EXCLUDED)

        mayo = por_mes["2026-05-01"]
        assert Decimal(mayo["ingresos"]) == Decimal("50.0000")  # anulada EXCLUDED
        assert Decimal(mayo["gastos"]) == Decimal("0.0000")  # zero-filled

        junio = por_mes["2026-06-01"]
        assert Decimal(junio["ingresos"]) == Decimal("0.0000")  # no sales that month
        assert Decimal(junio["gastos"]) == Decimal("30.0000")
    finally:
        _cleanup_ventas(v_ids)
        _cleanup_movimientos(mov_ids)
        _cleanup_producto(prod_id)
        _cleanup_insumo(ins_id)
        _cleanup_categoria(cat_id)
        _cleanup_tipo(tipo_id)
