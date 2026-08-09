"""Analiticos API endpoint tests — strict TDD (slice 3, tasks 3.1 + 3.4).

Drives the three read-only analytics endpoints through the FastAPI TestClient
against the real test PostgreSQL:
- GET /analiticos/ventas-mensuales: GROUP BY month, SUM(total_venta) + count,
  EXCLUDING anulada sales (ANA-1).
- GET /analiticos/insumos-bajo-stock: only insumos with stock_actual <
  stock_minimo, with their minima (ANA-2).
- GET /analiticos/margen-por-producto: margin from the
  Detalle_Ventas.costo_unitario_aplicado SNAPSHOT (never the current WAC),
  excluding anulada lines (ANA-3).

All three are read-only and audited: 401 without token, 200 for admin /
operador / consulta. Sales are inserted directly with explicit `fecha` values
so the monthly grouping and anulada-exclusion are deterministic; the current
WAC is set to a value DIFFERENT from every snapshot to prove the snapshot-only
rule. FK-ordered cleanup.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    DetalleVenta,
    Insumo,
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
                cantidad=Decimal("1"),
                precio_unitario_aplicado=Decimal(precio),
                costo_unitario_aplicado=Decimal(costo),
            )
        )
        db.commit()
        return venta.id
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
    """Two months: 2027-01 has 2 completada (100+200), 2027-02 has 1 completada
    (50) + 1 anulada (9999) -> totals/counts only include non-anulada rows
    (ANA-1). Los meses 2027 no colisionan con las ventas reales de la migracion
    cargada (2025-12..2026-05), asi el total por mes es determinista."""
    cat_id = _make_categoria()
    ins_id = _make_insumo(cat_id, costo="999", stock="0")  # current WAC 999
    tipo_id = _make_tipo()
    prod_id = _make_producto(tipo_id)
    _make_linea_insumo(prod_id, ins_id)
    try:
        v_ids = [
            _insertar_venta(prod_id, datetime(2027, 1, 15, 12, 0, 0), "100", precio="100", costo="60"),
            _insertar_venta(prod_id, datetime(2027, 1, 20, 12, 0, 0), "200", precio="100", costo="70"),
            _insertar_venta(prod_id, datetime(2027, 2, 5, 12, 0, 0), "50", precio="100", costo="50"),
            _insertar_venta(prod_id, datetime(2027, 2, 10, 12, 0, 0), "9999", estado="anulada", precio="100", costo="10"),
        ]
        resp = client.get(
            "/api/v1/analiticos/ventas-mensuales", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        por_mes = {r["mes"]: r for r in resp.json()}

        enero = por_mes["2027-01-01"]
        assert Decimal(enero["total"]) == Decimal("300.0000")  # 100 + 200
        assert enero["cantidad"] == 2

        febrero = por_mes["2027-02-01"]
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
