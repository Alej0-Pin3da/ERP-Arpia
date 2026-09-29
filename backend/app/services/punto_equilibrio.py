"""Termómetro Operativo del Mes — break-even from real month sales.

- Month bounds forced to America/Bogota so 1st-of-month dawn sales never
  fall into the previous month (no bare UTC anywhere here).
- Only `confirmed` sales count; draft/cancelled/reversed are ignored.
- Confirmed devoluciones of the month are netted from BOTH sides: income
  via monto_reembolsado, cost by matching returned items against the
  original sale detalles (producto+variante) at their costo_unitario_aplicado.
- Strict Decimal throughout; no floats touch money.
"""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.maestros import ParametrosCosteo
from app.models.ventas import Devolucion, Venta
from app.schemas.punto_equilibrio import PuntoEquilibrioRead

BOGOTA = ZoneInfo("America/Bogota")
_CENT = Decimal("0.01")
_PCT = Decimal("0.1")


def _bounds_bogota(ahora: datetime) -> tuple[datetime, datetime]:
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=BOGOTA)
    inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)
    return inicio, fin


def _costo_devuelto(dev: Devolucion) -> Decimal:
    """Cost side of a return, matched against the original sale detalles.

    Remaining quantities are consumed in row order so a partial return never
    nets more cost than the sale carried. Unknown lines contribute 0 (never
    invented).
    """
    restantes: dict[tuple[int, int | None], list[Decimal]] = {}
    for d in dev.venta.detalles or []:
        key = (d.producto_id, d.variante_id)
        slot = restantes.setdefault(key, [Decimal("0"), Decimal("0")])
        slot[0] += d.cantidad or Decimal("0")
        slot[1] = d.costo_unitario_aplicado or Decimal("0")
    total = Decimal("0")
    for it in dev.items or []:
        slot = restantes.get((it.producto_id, it.variante_id))
        if slot is None:
            continue
        toma = min(it.cantidad or Decimal("0"), slot[0])
        if toma > 0:
            total += toma * slot[1]
            slot[0] -= toma
    return total


def calcular_termometro(db: Session, ahora: datetime | None = None) -> PuntoEquilibrioRead:
    ref = ahora or datetime.now(BOGOTA)
    inicio, fin = _bounds_bogota(ref)
    periodo = f"{inicio.year:04d}-{inicio.month:02d}"

    ventas = list(
        db.scalars(
            select(Venta)
            .where(Venta.estado == "confirmed", Venta.fecha >= inicio, Venta.fecha < fin)
            .options(selectinload(Venta.detalles))
        ).all()
    )
    ingreso = sum((v.total_venta or Decimal("0") for v in ventas), Decimal("0"))
    costo = sum((v.costo_total for v in ventas), Decimal("0"))

    devs = list(
        db.scalars(
            select(Devolucion)
            .where(Devolucion.estado == "confirmed", Devolucion.fecha >= inicio, Devolucion.fecha < fin)
            .options(
                selectinload(Devolucion.items),
                selectinload(Devolucion.venta).selectinload(Venta.detalles),
            )
        ).all()
    )
    dev_ingreso = sum((d.monto_reembolsado or Decimal("0") for d in devs), Decimal("0"))
    dev_costo = sum((_costo_devuelto(d) for d in devs), Decimal("0"))

    ventas_netas = ingreso - dev_ingreso
    costos_netos = costo - dev_costo
    n_ventas = len(ventas)
    n_devoluciones = len(devs)

    row = db.get(ParametrosCosteo, 1)
    fijos = (row.costos_fijos_mensuales if row is not None else None) or Decimal("0")

    base = {
        "periodo": periodo,
        "ventas_netas": ventas_netas,
        "costos_netos": costos_netos,
        "costos_fijos": fijos,
        "n_ventas": n_ventas,
        "n_devoluciones": n_devoluciones,
    }
    vacio = {
        "meta_ventas": None,
        "avance_pct": None,
        "faltante": None,
        "utilidad_extra": None,
    }

    if n_ventas == 0 and n_devoluciones == 0:
        return PuntoEquilibrioRead(estado="sin_datos", margen_pct=Decimal("0"), **vacio, **base)

    if ventas_netas <= 0:
        return PuntoEquilibrioRead(estado="alerta", margen_pct=Decimal("0"), **vacio, **base)
    margen_frac = (ventas_netas - costos_netos) / ventas_netas
    margen_pct = (margen_frac * Decimal("100")).quantize(_PCT)
    if margen_frac <= 0:
        return PuntoEquilibrioRead(estado="alerta", margen_pct=margen_pct, **vacio, **base)

    if fijos <= 0:
        return PuntoEquilibrioRead(estado="sin_configurar", margen_pct=margen_pct, **vacio, **base)

    meta = (fijos / margen_frac).quantize(_CENT)
    avance = (ventas_netas / meta * Decimal("100")).quantize(_PCT)
    if ventas_netas >= meta:
        return PuntoEquilibrioRead(
            estado="superada",
            margen_pct=margen_pct,
            meta_ventas=meta,
            avance_pct=avance,
            faltante=None,
            utilidad_extra=(ventas_netas - meta).quantize(_CENT),
            **base,
        )
    return PuntoEquilibrioRead(
        estado="en_camino",
        margen_pct=margen_pct,
        meta_ventas=meta,
        avance_pct=avance,
        faltante=(meta - ventas_netas).quantize(_CENT),
        utilidad_extra=None,
        **base,
    )
