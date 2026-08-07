"""Analiticos API routes — three read-only aggregation endpoints (ANA-1..3).

All queries run against snapshot data only:
- ventas-mensuales: SUM(total_venta) + count per month, EXCLUDING anuladas.
- insumos-bajo-stock: insumos where stock_actual < stock_minimo.
- margen-por-producto: SUM/AVG(precio - costo_unitario_aplicado) per
  (producto, variante) from the Detalle_Ventas snapshot — NEVER the current
  WAC — excluding anulada lines.

Read-only + audited: admin|operador|consulta. No commits, no locks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.insumos import Insumo
from app.models.ventas import DetalleVenta, Venta
from app.schemas.analiticos import (
    InsumoBajoStockRead,
    MargenProductoRead,
    VentasMensualesRead,
)

router = APIRouter(prefix="/analiticos", tags=["analiticos"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("/ventas-mensuales", response_model=list[VentasMensualesRead])
def ventas_mensuales(
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Monthly sales aggregation: per month, SUM(total_venta) and sale count,
    excluding anulada sales (ANA-1)."""
    # One expression object reused in SELECT/GROUP BY/ORDER BY so SQLAlchemy
    # binds 'month' identically in every occurrence (distinct bind params
    # would make PostgreSQL treat them as different GROUP BY expressions).
    mes = func.date_trunc("month", Venta.fecha)
    rows = db.execute(
        select(
            mes.label("mes"),
            func.coalesce(func.sum(Venta.total_venta), 0).label("total"),
            func.count(Venta.id).label("cantidad"),
        )
        .where(Venta.estado != "anulada")
        .group_by(mes)
        .order_by(mes)
    ).all()
    return [
        VentasMensualesRead(mes=r.mes.date(), total=r.total, cantidad=r.cantidad)
        for r in rows
    ]


@router.get("/insumos-bajo-stock", response_model=list[InsumoBajoStockRead])
def insumos_bajo_stock(
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Insumos whose stock_actual is below stock_minimo, with their minima
    (ANA-2)."""
    rows = db.scalars(
        select(Insumo)
        .where(Insumo.stock_actual < Insumo.stock_minimo)
        .order_by(Insumo.id)
    ).all()
    return [
        InsumoBajoStockRead(
            insumo_id=insumo.id,
            nombre=insumo.nombre,
            unidad_medida=insumo.unidad_medida,
            stock_actual=insumo.stock_actual,
            stock_minimo=insumo.stock_minimo,
        )
        for insumo in rows
    ]


@router.get("/margen-por-producto", response_model=list[MargenProductoRead])
def margen_por_producto(
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Margin per (producto, variante): SUM and AVG of
    (precio - costo_unitario_aplicado) from the Detalle_Ventas SNAPSHOT only,
    excluding anulada sales (ANA-3)."""
    margen = (
        DetalleVenta.precio_unitario_aplicado - DetalleVenta.costo_unitario_aplicado
    )
    rows = db.execute(
        select(
            DetalleVenta.producto_id,
            DetalleVenta.variante_id,
            cast(func.sum(margen), Numeric(15, 4)).label("margen_total"),
            cast(func.avg(margen), Numeric(15, 4)).label("margen_promedio"),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(Venta.estado != "anulada")
        .group_by(DetalleVenta.producto_id, DetalleVenta.variante_id)
        .order_by(DetalleVenta.producto_id)
    ).all()
    return [
        MargenProductoRead(
            producto_id=r.producto_id,
            variante_id=r.variante_id,
            margen_total=r.margen_total,
            margen_promedio=r.margen_promedio,
        )
        for r in rows
    ]
