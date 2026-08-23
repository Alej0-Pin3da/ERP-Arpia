"""Analiticos API routes — six read-only aggregation endpoints (ANA-1..6).

All queries run against snapshot data only:
- ventas-mensuales: SUM(total_venta) + count per month, EXCLUDING anuladas.
- insumos-bajo-stock: insumos where stock_actual < stock_minimo.
- margen-por-producto: SUM/AVG(precio - costo_unitario_aplicado) per
  (producto, variante) from the Detalle_Ventas snapshot — NEVER the current
  WAC — excluding anulada lines.
- top-productos: SUM(cantidad) + SUM(cantidad * precio_unitario_aplicado) per
  product from the Detalle_Ventas snapshot, excluding anulada lines.
- top-insumos: SUM(cantidad_comprada) per insumo from Compras_Insumos (the
  DB has no production/consumption ledger, so purchases are the real proxy).
- finanzas-mensuales: per-month SUM(total_venta) as ingresos vs SUM(monto) of
  ACTIVE Gasto|Inversion Movimientos_Financieros as gastos.

Read-only + audited: admin|operador|consulta. No commits, no locks.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.finanzas import MovimientoFinanciero
from app.models.insumos import CompraInsumo, Insumo
from app.models.ventas import DetalleVenta, DocumentState, Venta
from app.schemas.analiticos import (
    AnaliticosResumenRead,
    FinanzasMensualesRead,
    InsumoBajoStockRead,
    MargenProductoRead,
    TopInsumoRead,
    TopProductoRead,
    VentasMensualesRead,
)

router = APIRouter(prefix="/analiticos", tags=["analiticos"])

audited_user = require_roles("admin", "operador", "consulta")
FOUR_DECIMALS = Decimal("0.0001")


def _period_bounds(desde: date | None, hasta: date | None) -> tuple[date, date]:
    hoy = date.today()
    if desde is None and hasta is None:
        return hoy.replace(day=1), hoy
    if desde is None or hasta is None or desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El periodo requiere desde y hasta válidos, con desde <= hasta.",
        )
    return desde, hasta


def _utc_range(desde: date, hasta: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(desde, time.min, tzinfo=UTC),
        datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=UTC),
    )


def _optional_range(desde: date | None, hasta: date | None) -> tuple[datetime, datetime] | None:
    if desde is None and hasta is None:
        return None
    inicio, fin = _period_bounds(desde, hasta)
    return _utc_range(inicio, fin)


def _resumen_periodo(db: Session, desde: date, hasta: date) -> dict[str, Decimal | int]:
    inicio, fin = _utc_range(desde, hasta)
    ventas_filter = (
        Venta.fecha >= inicio,
        Venta.fecha < fin,
        Venta.estado != DocumentState.CANCELLED.value,
        Venta.es_regalo.is_(False),
    )
    ventas_total, cantidad_ventas = db.execute(
        select(
            func.coalesce(func.sum(Venta.total_venta), 0),
            func.count(Venta.id),
        ).where(*ventas_filter)
    ).one()
    unidades_vendidas = db.scalar(
        select(func.coalesce(func.sum(DetalleVenta.cantidad), 0))
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(*ventas_filter)
    ) or Decimal("0")
    margen_total = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    DetalleVenta.cantidad
                    * (DetalleVenta.precio_unitario_aplicado - DetalleVenta.costo_unitario_aplicado)
                ),
                0,
            )
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(*ventas_filter)
    ) or Decimal("0")
    gastos_total = db.scalar(
        select(func.coalesce(func.sum(MovimientoFinanciero.monto), 0)).where(
            MovimientoFinanciero.fecha >= inicio,
            MovimientoFinanciero.fecha < fin,
            MovimientoFinanciero.tipo.in_(("Gasto", "Inversion")),
            MovimientoFinanciero.estado == DocumentState.CONFIRMED.value,
        )
    ) or Decimal("0")
    ventas_total = Decimal(ventas_total or 0).quantize(FOUR_DECIMALS)
    cantidad_ventas = int(cantidad_ventas or 0)
    unidades_vendidas = Decimal(unidades_vendidas).quantize(FOUR_DECIMALS)
    margen_total = Decimal(margen_total).quantize(FOUR_DECIMALS)
    gastos_total = Decimal(gastos_total).quantize(FOUR_DECIMALS)
    return {
        "ventas_total": ventas_total,
        "cantidad_ventas": cantidad_ventas,
        "unidades_vendidas": unidades_vendidas,
        "ticket_promedio": ventas_total / cantidad_ventas if cantidad_ventas else Decimal("0"),
        "margen_total": margen_total,
        "gastos_total": gastos_total,
        "resultado_neto": margen_total - gastos_total,
    }


@router.get("/resumen", response_model=AnaliticosResumenRead)
def resumen(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Summary for a selected period plus the immediately preceding period."""
    desde, hasta = _period_bounds(desde, hasta)
    dias = (hasta - desde).days + 1
    anterior_hasta = desde - timedelta(days=1)
    anterior_desde = anterior_hasta - timedelta(days=dias - 1)
    actual = _resumen_periodo(db, desde, hasta)
    anterior = _resumen_periodo(db, anterior_desde, anterior_hasta)
    return AnaliticosResumenRead(
        desde=desde,
        hasta=hasta,
        **actual,
        unidades_periodo_anterior=anterior["unidades_vendidas"],
        ticket_periodo_anterior=anterior["ticket_promedio"],
        ventas_periodo_anterior=anterior["ventas_total"],
        margen_periodo_anterior=anterior["margen_total"],
        gastos_periodo_anterior=anterior["gastos_total"],
        resultado_periodo_anterior=anterior["resultado_neto"],
    )


@router.get("/ventas-mensuales", response_model=list[VentasMensualesRead])
def ventas_mensuales(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Monthly sales aggregation: per month, SUM(total_venta) and sale count,
    excluding anulada sales (ANA-1)."""
    # One expression object reused in SELECT/GROUP BY/ORDER BY so SQLAlchemy
    # binds 'month' identically in every occurrence (distinct bind params
    # would make PostgreSQL treat them as different GROUP BY expressions).
    mes = func.date_trunc("month", Venta.fecha)
    condiciones = [Venta.estado != DocumentState.CANCELLED.value, Venta.es_regalo.is_(False)]
    rango = _optional_range(desde, hasta)
    if rango is not None:
        condiciones.extend([Venta.fecha >= rango[0], Venta.fecha < rango[1]])
    rows = db.execute(
        select(
            mes.label("mes"),
            func.coalesce(func.sum(Venta.total_venta), 0).label("total"),
            func.count(Venta.id).label("cantidad"),
        )
        .where(*condiciones)
        .group_by(mes)
        .order_by(mes)
    ).all()
    return [VentasMensualesRead(mes=r.mes.date(), total=r.total, cantidad=r.cantidad) for r in rows]


@router.get("/insumos-bajo-stock", response_model=list[InsumoBajoStockRead])
def insumos_bajo_stock(
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Insumos whose stock_actual is below stock_minimo, with their minima
    (ANA-2)."""
    rows = db.scalars(
        select(Insumo).where(Insumo.stock_actual < Insumo.stock_minimo).order_by(Insumo.id)
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
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Margin per (producto, variante): SUM and AVG of
    (precio - costo_unitario_aplicado) from the Detalle_Ventas SNAPSHOT only,
    excluding anulada sales (ANA-3)."""
    margen = DetalleVenta.precio_unitario_aplicado - DetalleVenta.costo_unitario_aplicado
    condiciones = [Venta.estado != DocumentState.CANCELLED.value, Venta.es_regalo.is_(False)]
    rango = _optional_range(desde, hasta)
    if rango is not None:
        condiciones.extend([Venta.fecha >= rango[0], Venta.fecha < rango[1]])
    rows = db.execute(
        select(
            DetalleVenta.producto_id,
            DetalleVenta.variante_id,
            cast(func.sum(margen), Numeric(15, 4)).label("margen_total"),
            cast(func.avg(margen), Numeric(15, 4)).label("margen_promedio"),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(*condiciones)
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


@router.get("/top-productos", response_model=list[TopProductoRead])
def top_productos(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Top products by units sold: SUM(cantidad) and SUM(cantidad *
    precio_unitario_aplicado) per product from the Detalle_Ventas SNAPSHOT,
    excluding anulada lines — ordered by units desc (ANA-4)."""
    # One expression object reused in SELECT/ORDER BY so SQLAlchemy binds the
    # aggregate identically in every occurrence.
    unidades_total = func.sum(DetalleVenta.cantidad)
    ingresos_total = func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario_aplicado)
    condiciones = [Venta.estado != DocumentState.CANCELLED.value, Venta.es_regalo.is_(False)]
    rango = _optional_range(desde, hasta)
    if rango is not None:
        condiciones.extend([Venta.fecha >= rango[0], Venta.fecha < rango[1]])
    rows = db.execute(
        select(
            DetalleVenta.producto_id,
            cast(unidades_total, Numeric(15, 4)).label("unidades"),
            cast(ingresos_total, Numeric(15, 4)).label("ingresos"),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(*condiciones)
        .group_by(DetalleVenta.producto_id)
        .order_by(unidades_total.desc(), DetalleVenta.producto_id)
    ).all()
    return [
        TopProductoRead(
            producto_id=r.producto_id,
            unidades=r.unidades,
            ingresos=r.ingresos,
        )
        for r in rows
    ]


@router.get("/top-insumos", response_model=list[TopInsumoRead])
def top_insumos(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Insumos by total quantity purchased: SUM(cantidad_comprada) per insumo
    from Compras_Insumos, with the joined name and unit of measure — ordered
    by quantity desc (ANA-5). Compras_Insumos is the real consumption proxy;
    the DB has no production/consumption ledger."""
    cantidad_total = func.sum(CompraInsumo.cantidad_comprada)
    condiciones = []
    rango = _optional_range(desde, hasta)
    if rango is not None:
        condiciones.extend(
            [CompraInsumo.fecha_compra >= rango[0], CompraInsumo.fecha_compra < rango[1]]
        )
    rows = db.execute(
        select(
            CompraInsumo.insumo_id,
            Insumo.nombre,
            Insumo.unidad_medida,
            cast(cantidad_total, Numeric(15, 4)).label("cantidad"),
        )
        .join(Insumo, CompraInsumo.insumo_id == Insumo.id)
        .where(*condiciones)
        .group_by(CompraInsumo.insumo_id, Insumo.nombre, Insumo.unidad_medida)
        .order_by(cantidad_total.desc(), CompraInsumo.insumo_id)
    ).all()
    return [
        TopInsumoRead(
            insumo_id=r.insumo_id,
            nombre=r.nombre,
            unidad_medida=r.unidad_medida,
            cantidad=r.cantidad,
        )
        for r in rows
    ]


@router.get("/finanzas-mensuales", response_model=list[FinanzasMensualesRead])
def finanzas_mensuales(
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(audited_user),
):
    """Monthly Ingresos (SUM of non-anulada Ventas.total_venta) vs Gastos
    (SUM of monto for ACTIVE Gasto|Inversion Movimientos_Financieros — Retiros
    and soft-deleted rows are excluded). One row per calendar month that has
    either side present; the missing side is zero-filled (ANA-6)."""
    mes_ventas = func.date_trunc("month", Venta.fecha)
    mes_movimientos = func.date_trunc("month", MovimientoFinanciero.fecha)

    rango = _optional_range(desde, hasta)
    ventas_condiciones = [Venta.estado != DocumentState.CANCELLED.value, Venta.es_regalo.is_(False)]
    movimientos_condiciones = [
        MovimientoFinanciero.tipo.in_(("Gasto", "Inversion")),
        MovimientoFinanciero.estado == DocumentState.CONFIRMED.value,
    ]
    if rango is not None:
        ventas_condiciones.extend([Venta.fecha >= rango[0], Venta.fecha < rango[1]])
        movimientos_condiciones.extend(
            [MovimientoFinanciero.fecha >= rango[0], MovimientoFinanciero.fecha < rango[1]]
        )
    ventas_rows = db.execute(
        select(
            mes_ventas.label("mes"),
            func.coalesce(func.sum(Venta.total_venta), 0).label("ingresos"),
        )
        .where(*ventas_condiciones)
        .group_by(mes_ventas)
    ).all()
    movimientos_rows = db.execute(
        select(
            mes_movimientos.label("mes"),
            func.coalesce(func.sum(MovimientoFinanciero.monto), 0).label("gastos"),
        )
        .where(*movimientos_condiciones)
        .group_by(mes_movimientos)
    ).all()

    por_mes: dict[date, dict[str, date | Decimal]] = {}
    for r in ventas_rows:
        por_mes.setdefault(
            r.mes.date(),
            {"mes": r.mes.date(), "ingresos": Decimal("0"), "gastos": Decimal("0")},
        )["ingresos"] = r.ingresos
    for r in movimientos_rows:
        por_mes.setdefault(
            r.mes.date(),
            {"mes": r.mes.date(), "ingresos": Decimal("0"), "gastos": Decimal("0")},
        )["gastos"] = r.gastos

    return [FinanzasMensualesRead(**por_mes[mes]) for mes in sorted(por_mes)]
